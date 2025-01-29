import os
import glob
import datetime as dt
import numpy as np
import xarray as xr
import rioxarray
import rioxarray.merge
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from pystac_client import Client
from rioxarray.merge import merge_arrays


# ------------------------------------------------------------------------------
# 1. Environment and Geometry Setup
# ------------------------------------------------------------------------------
def setup_environment(working_directory):
    """
    Sets the working directory for the project.
    """
    os.chdir(working_directory)
    print(f"Working directory set to: {os.getcwd()}")

def load_county_geometry(fips_code):
    """
    Loads the geometry for a specified county based on its FIPS code from the Montana TIGER shapefile.
    
    Parameters:
    fips_code (str): The FIPS code of the county to load. MSO County = 063
    
    Returns:
    geopandas.GeoDataFrame: A GeoDataFrame containing the combined geometry of the specified county.
    
    """
    
    # Load mso county TIGER shapefile
    mso_county = gpd.read_file("vector_data/montana_TIGER/tl_2022_30_tabblock20/tl_2022_30_tabblock20.shp")

    # Filter for the specified county FIPS code
    filtered_county = mso_county[(mso_county['COUNTYFP20'] == fips_code)]
    combined_county = filtered_county.dissolve(by='COUNTYFP20')
    geometry_umt = combined_county.to_crs("EPSG:32611")
    return combined_county, geometry_umt

setup_environment("/Volumes/Drew_ext_drive/NDVI_Proj")
geometry, geometry_utm = load_county_geometry('063')
# setup_environment("/Volumes/Drew_ext_drive/NDVI_Proj")
# mso_county = load_county_geometry('063')
# ------------------------------------------------------------------------------
# 2. STAC Searching
# ------------------------------------------------------------------------------
def search_sentinel_scenes(date_str, geometry, collection, client):
    """
    Uses the STAC client to search Sentinel-2 scenes intersecting the input geometry,
    on the given date. Returns an ItemCollection if any scenes are found, otherwise None.
    """
    search = client.search(
        collections=[collection],
        bbox=geometry['geometry'].union_all().bounds, # This converts the geopandas dataframe into a bounding box tuple
        datetime=date_str
    )
    
    if search.matched() > 0:
        items = search.item_collection()
        print(f"{len(items)} Scenes matched for {date_str}")
        return items
    else:
        print(f"No Scenes found for {date_str}")
        return None


# search_sentinel_scenes("2024-07-26", geometry, "sentinel-2-l2a", client)
# ------------------------------------------------------------------------------
# 3. Band Clipping and Masking
# ------------------------------------------------------------------------------
def clip_band(band_url, clip_geometry, target_crs="EPSG:32611"):
    """
    This function opens a band from a STAC asset, reprojects to target_crs if needed,
    then clips it to the clip_geometry.
    
    Parameters:
    band_url (str): The URL of the band to be opened.
    clip_geometry (geopandas.GeoDataFrame): The geometry to clip the band to.
    target_crs (str, optional): The target CRS to reproject the band to. Defaults to "EPSG:32611".
    
    Returns:
    rioxarray.DataArray: The clipped band.
    """
    band = rioxarray.open_rasterio(band_url, chunks={"x": 1024, "y": 1024})
    
    if band.rio.crs != target_crs:
        band = band.rio.reproject(target_crs)
    
    band = band.rio.clip(clip_geometry.geometry.tolist(), crs=clip_geometry.crs)
    return band

# items = search_sentinel_scenes("2024-07-26", geometry, "sentinel-2-l2a", client)
# scene = items[0]
# red_band = clip_band(scene.assets['red'].href, geometry_utm)
def get_vegetation_pixels(target_band, scl_band, target_crs="EPSG:32611"):
    """
    Masks the target_band (Red or NIR) to include only vegetation pixels
    using the SCL band (value == 4).
    
    Parameters:
    target_band (rioxarray.DataArray): The target band to be masked.
    scl_band (rioxarray.DataArray): The SCL band to be used for masking.
    target_crs (str, optional): The target CRS to reproject the band to. Defaults to "EPSG:32611".
    
    Returns:
    rioxarray.DataArray: The masked band.
    """
    if scl_band.rio.crs != target_crs:
        scl_band = scl_band.rio.reproject(target_crs)
        
    if target_band.rio.crs != target_crs:
        target_band = target_band.rio.reproject(target_crs)
    
    scl_resampled = scl_band.rio.reproject_match(target_band)  # Resample to match resolution
    vegetation_mask = scl_resampled == 4  # Identify vegetation pixels
    band_masked = target_band.where(vegetation_mask)
    
    return band_masked


### CHAT GPT TRY
def get_vegetation_pixels(target_band, scl_band, clip_geometry, target_crs="EPSG:32611"):
    """
    Masks the target_band (Red or NIR) to include only vegetation pixels
    using the SCL band (value == 4), after clipping the bands to the specified geometry.
    
    Parameters:
    target_band (rioxarray.DataArray): The target band to be masked.
    scl_band (rioxarray.DataArray): The SCL band to be used for masking.
    clip_geometry (geometry): The geometry to clip the bands to.
    target_crs (str, optional): The target CRS to reproject the band to. Defaults to "EPSG:32611".
    
    Returns:
    rioxarray.DataArray: The masked band.
    """
    if scl_band.rio.crs != target_crs:
        scl_band = scl_band.rio.reproject(target_crs)
    
    # Clip the scl_band to the specified geometry
    scl_band = scl_band.rio.clip([clip_geometry], crs=target_crs)

    # Resample SCL to match the resolution of target_band
    scl_resampled = scl_band.rio.reproject_match(target_band)
    vegetation_mask = scl_resampled == 4  # Create a mask for vegetation pixels
    band_masked = target_band.where(vegetation_mask)  # Apply the mask to the band
    
    return band_masked



def clip_and_mask_bands(scene, geometry_utm):
    """
    From a STAC scene, clip and mask the Red, NIR, and SCL bands.
    Returns: (red_band_masked, nir_band_masked)
    
    Parameters:
    scene (dict): A STAC scene containing assets.
    geometry_utm (geopandas.GeoDataFrame): The geometry to clip the bands to in UTM projection.
    
    Returns:
    rioxarray.DataArray: The clipped and masked Red band.
    """
    assets = scene.assets
    # Clip Red and NIR
    red_band = clip_band(assets['red'].href, geometry_utm)
    nir_band = clip_band(assets['nir'].href, geometry_utm)
    
    # Load SCL (mask layer)
    scl_band = clip_band(assets['scl'].href, geometry_utm)
    
    # Mask Red and NIR for vegetation
    red_band_masked = get_vegetation_pixels(red_band, scl_band, geometry_utm)
    nir_band_masked = get_vegetation_pixels(nir_band, scl_band, geometry_utm)
    
    # Align both raster layers
    red_band_masked, nir_band_masked = xr.align(red_band_masked, nir_band_masked)
    return red_band_masked, nir_band_masked


# ------------------------------------------------------------------------------
# 4. NDVI Computation and Saving
# ------------------------------------------------------------------------------
def compute_ndvi(red_band_masked, nir_band_masked):
    """
    Computes the NDVI: (NIR - Red) / (NIR + Red) for non-NaN,
    sets result to 0 where the denominator is 0, else NaN if inputs are NaN.
    
    Parameters:
    red_band_masked (rioxarray.DataArray): The masked Red band.
    nir_band_masked (rioxarray.DataArray): The masked NIR band.
    
    Returns:
    rioxarray.DataArray: The computed NDVI.
    """
    ndvi = xr.where(
        ~xr.ufuncs.isnan(nir_band_masked) & ~xr.ufuncs.isnan(red_band_masked),
        xr.where(
            (nir_band_masked + red_band_masked) > 0,
            (nir_band_masked - red_band_masked) / (nir_band_masked + red_band_masked),
            0  # Assign 0 when denominator is 0
        ),
        np.nan  # Assign NaN if either band is NaN
    )
    # Retain the CRS from the red band (arbitrary choice, as both are aligned)
    ndvi = ndvi.rio.write_crs(red_band_masked.rio.crs)
    return ndvi

def save_raster(raster, band_name, scene_id, output_path):
    """
    Saves a raster to disk as GeoTIFF.
    
    Parameters:
    raster (rioxarray.DataArray): The raster to be saved.
    band_name (str): The name of the band to be used in the output file name.
    scene_id (str): The ID of the scene to be used in the output file name.
    output_path (str): The directory where the raster will be saved.
    """
    output_file = f"{output_path}/{band_name}_{scene_id}.tif"
    raster.rio.to_raster(
        output_file,
        driver="GTiff",
        compress="LZW",
        tiled=True,
        blockxsize=256,
        blockysize=256
    )
    print(f"Saved {band_name} raster to {output_file}")


# ------------------------------------------------------------------------------
# 5. Mosaic Creation
# ------------------------------------------------------------------------------
def create_mosaic(band_name, output_path, target_crs="EPSG:32611"):
    """
    Gathers all raster files matching band_name in output_path,
    merges them, reprojects to target_crs if needed,
    and saves the mosaic as a GeoTIFF.
    
    Parameters:
    band_name (str): The name of the band to be used for file matching.
    output_path (str): The directory where the raster files are located.
    target_crs (str, optional): The target Coordinate Reference System for reprojection. Defaults to "EPSG:32611".
    """
    band_files = glob.glob(f"{output_path}/{band_name}_*.tif")
    if not band_files:
        print(f"No {band_name} raster files found in {output_path}. Mosaic not created.")
        return
    
    # Open all the rasters into a list
    raster_list = [rioxarray.open_rasterio(file, chunks={"x": 1024, "y": 1024}) for file in band_files]
    
    # Merge the rasters
    mosaic = merge_arrays(raster_list)
    mosaic = mosaic.compute()
    
    # Reproject the mosaic to ensure CRS consistency
    mosaic = mosaic.rio.reproject(target_crs)
    
    # Save the final mosaic
    mosaic_file = f"{output_path}/{band_name}_merged.tif"
    mosaic.rio.to_raster(
        mosaic_file,
        driver="GTiff",
        compress="LZW",
        tiled=True,
        blockxsize=256,
        blockysize=256
    )
    print(f"{band_name} mosaic saved to {mosaic_file}")

def combine_layers(output_path):
    """
    Combines the red, green, blue, and NDVI bands into a single multi-band raster and saves it.
    
    Parameters:
    output_path (str): The directory where the raster files are located.
    """
    # Open each band
    red = rioxarray.open_rasterio(f"{output_path}/red_merged", chunks={"x": 1024, "y": 1024})
    green = rioxarray.open_rasterio(f"{output_path}/green_merged", chunks={"x": 1024, "y": 1024})
    blue = rioxarray.open_rasterio(f"{output_path}/blue_merged", chunks={"x": 1024, "y": 1024})
    ndvi = rioxarray.open_rasterio(f"{output_path}/NDVI_merged", chunks={"x": 1024, "y": 1024})
    
    # Stack bands into a single multi-band raster
    rgb_mosaic = xr.concat([red, green, blue, ndvi], dim="band")
    
    # Save the final RGB mosaic
    rgb_mosaic.rio.to_raster(output_path, compress="LZW")
    print(f"Multiband raster saved to {output_path}")
# ------------------------------------------------------------------------------
# 6. Main Workflow
# ------------------------------------------------------------------------------
def process_date(date_str, geometry, geometry_utm, collection, client):
    """
    Searches for Sentinel-2 scenes for the given date,
    processes them by computing and saving NDVI,
    then calls create_mosaic.
    """
    items = search_sentinel_scenes(date_str, geometry, collection, client)
    if not items:
        return  # No scenes to process for this date
    
    # Parse date components for output folder naming
    date_obj = dt.datetime.strptime(date_str, "%Y-%m-%d")
    month = date_obj.strftime("%B")
    day = date_obj.strftime("%d")
    
    # Create output directory
    output_path = f"historic_rasters/2024/{month}/{day}"
    os.makedirs(output_path, exist_ok=True)
    
    # Process each scene
    for scene in items:
        print(f"Processing scene ID: {scene.id}")
        
        red_band = clip_band(scene.assets['red'].href, geometry_utm)
        save_raster(red_band, 'red', scene.id, output_path)
        blue_band = clip_band(scene.assets['blue'].href, geometry_utm)
        save_raster(blue_band, 'blue', scene.id, output_path)
        green_band = clip_band(scene.assets['green'].href, geometry_utm)
        save_raster(green_band, 'green', scene.id, output_path)
        
        red_band_masked, nir_band_masked = clip_and_mask_bands(scene, geometry_utm)
        
        ndvi = compute_ndvi(red_band_masked, nir_band_masked)
        save_raster(ndvi, 'NDVI', scene.id, output_path)
    
    # After all scenes are processed, create a mosaic
    create_mosaic("NDVI", output_path)
    create_mosaic("red", output_path)
    create_mosaic("green", output_path)
    create_mosaic("blue", output_path)

    combine_layers(output_path)

def main():
    # 1. Set up environment & geometry
    working_directory = "/Volumes/Drew_ext_drive/NDVI_Proj"
    setup_environment(working_directory)
    
    geometry, geometry_utm = load_county_geometry('063')
    
    # 2. Initialize STAC client
    api_url = "https://earth-search.aws.element84.com/v1"
    client = Client.open(api_url)
    
    collection = "sentinel-2-l2a"
    
    # 3. Specify your target dates
    dates = ["2024-07-26"]  # Add more dates as needed
    
    # 4. Process each date
    for date_str in dates:
        process_date(date_str, geometry, geometry_utm, collection, client)

main()

