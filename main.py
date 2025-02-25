import os
import glob
import datetime as dt
import numpy as np
import xarray as xr
import rioxarray
import rioxarray.merge
import geopandas as gpd
import rasterio

from datetime import datetime, timedelta
from pystac_client import Client
from rioxarray.merge import merge_arrays
from rasterio.enums import Resampling
from upload_to_DO import connect_s3_client, upload_image_to_s3

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

# ------------------------------------------------------------------------------
# 2. STAC Searching
# ------------------------------------------------------------------------------
def search_sentinel_scenes(date_str, geometry, collection, client):
    """
    Uses the STAC client to search Sentinel-2 scenes intersecting the input geometry,
    on the given date. Returns an ItemCollection if any scenes are found if at least 
    one scene contains less than 80% cloud coverage, otherwise None.
    """
    search = client.search(
        collections=[collection],
        bbox=geometry['geometry'].union_all().bounds, # This converts the geopandas dataframe into a bounding box tuple
        datetime=date_str,
        query={"eo:cloud_cover": {"lt": 65}} # Looking for cloud coverage less than 65%
    )
    
    if search.matched() > 0:
        search = client.search(
        collections=[collection],
        bbox=geometry['geometry'].union_all().bounds, # This converts the geopandas dataframe into a bounding box tuple
        datetime=date_str 
        )
        items = search.item_collection()
        print(f"{len(items)} Scenes matched for {date_str}")
        return items
    else:
        print(f"No Scenes found for {date_str}")
        return None



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

def get_vegetation_pixels(target_band, scl_band, clip_geometry, target_crs="EPSG:32611"):
    """
    Masks the target_band (Red or NIR) to include only vegetation pixels
    using the SCL band (value == 4), after clipping the bands to the specified geometry.
    
    Parameters:
    target_band (rioxarray.DataArray): The target band to be masked.
    scl_band (rioxarray.DataArray): The SCL band to be used for masking.
    clip_geometry (geopandas.GeoDataFrame): The geometry to clip the bands to.
    target_crs (str, optional): The target CRS to reproject the band to. Defaults to "EPSG:32611".
    
    Returns:
    rioxarray.DataArray: The masked band.
    """
    if scl_band.rio.crs != target_crs:
        scl_band = scl_band.rio.reproject(target_crs)
    
    # Clip both bands to the specified geometry
    scl_band = scl_band.rio.clip(clip_geometry.geometry.tolist(), crs=target_crs, drop=False)
    target_band = target_band.rio.clip(clip_geometry.geometry.tolist(), crs=target_crs, drop=False)

    # Resample SCL to match the resolution of target_band
    scl_resampled = scl_band.rio.reproject_match(target_band)
    vegetation_mask = scl_resampled == 4  # Create a mask for vegetation pixels
    band_masked = target_band.where(vegetation_mask, np.nan)  # Apply the mask to the band
    
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
    sets result to nan where the denominator is 0, else NaN if inputs are NaN.
    
    Parameters:
    red_band_masked (rioxarray.DataArray): The masked Red band.
    nir_band_masked (rioxarray.DataArray): The masked NIR band.
    
    Returns:
    rioxarray.DataArray: The computed NDVI.
    """
    # Compute the numerator and denominator separately.
    numerator = nir_band_masked - red_band_masked
    denominator = nir_band_masked + red_band_masked

    # Use xr.where to avoid division when the denominator is zero.
    ndvi = xr.where(denominator == 0, np.nan, numerator / denominator)
    
    # Replace 0 values with NaN
    ndvi = np.where(ndvi == 0, np.nan, ndvi)
    
    
    # Ensure that pixels with NaNs in the original bands remain NaN.
    ndvi = xr.where(xr.ufuncs.isnan(red_band_masked) | xr.ufuncs.isnan(nir_band_masked), 
                    np.nan, ndvi)
    
    # Write the CRS from one of the bands.
    ndvi = ndvi.rio.write_crs(red_band_masked.rio.crs)

    return ndvi

def save_raster(raster, band, scene_id, output_path):
    """
    Saves a RGB raster to disk as Cloud Optimized GeoTIFF.
    
    Parameters:
    raster (rioxarray.DataArray): The raster to be saved.
    scene_id (str): The ID of the scene to be used in the output file name.
    output_path (str): The directory where the raster will be saved.
    """
    if band == 'RGB':
        output_file = f"{output_path}/RGB_{scene_id}.tif"
        photometric = 'RGB'
        dtype = 'uint8'
        nodata = None
    else:
        output_file = f"{output_path}/{band}_{scene_id}.tif"
        photometric = 'MINISBLACK'
        dtype = 'float32'
        nodata = np.nan
    
    raster = raster.astype(dtype) # Convert to 8-bit unsigned integer
    
    raster.rio.to_raster(
        output_file,
        driver="GTiff",
        compress="LZW",
        tiled=True,
        blockxsize=256,
        blockysize=256,
        photometric = photometric,
        predictor = 2,
        nodata = nodata,
        bigtiff = 'IF_SAFER',
        overview_resampling = 'average'
    )
    print(f"Saved {band} raster to {output_file}")


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
    

    mosaic = mosaic.compute() # Necessary to execute dask lazy execution (in chunks of 1024x1024)
    
    # Convert all 0 values to NaN
    mosaic = mosaic.where(mosaic != 0, np.nan)
    
    # Reproject the mosaic to ensure CRS consistency
    mosaic = mosaic.rio.reproject(target_crs)
    
    # Save the final mosaic
    save_raster(mosaic, band_name, "mosaic", output_path)
    
    
def rescale_band(band, scl_band=None, cloud_values=[3, 8, 9, 10, 11]): 
    """
    Rescales a band to 0-255 for visualization, excluding cloud, snow, and shadow pixels 
    if an SCL band is provided.
    
    Parameters:
        band (rioxarray.DataArray): The input band to rescale.
        scl_band (rioxarray.DataArray, optional): The scene classification layer used to mask out cloud pixels.
        cloud_values (list): List of SCL values representing clouds, snow, or shadows.
    
    Returns:
        rioxarray.DataArray: The rescaled band as an 8-bit unsigned integer array.
    """
    if scl_band is not None:
        # Resample the SCL band to match the resolution of the target band
        scl_resampled = scl_band.rio.reproject_match(band)
        
        # Create a mask: True for pixels NOT matching any cloud value
        mask = ~np.isin(scl_resampled.values, cloud_values)
        
        # Apply the mask to the band
        band_masked = band.where(mask, np.nan)
        
        # Extract valid pixels (non-cloud, non-shadow, etc.)
        valid_pixels = band_masked.values[~np.isnan(band_masked.values)]
    else:
        valid_pixels = band.values

    # Compute the 0.1th and 99.9th percentiles on valid (non-cloud) pixels
    p1, p99 = np.percentile(valid_pixels, [0.1, 99.9])

    if p99 - p1 == 0:
        raise ValueError("p99 - p1 is zero. Rescaling will produce NaN values.")

    # Apply linear rescaling
    band_rescaled = (band - p1) / (p99 - p1) * 255
    
    # Clip values to the valid range and replace NaN with 0
    band_rescaled = band_rescaled.clip(0, 255).where(~np.isnan(band), 0)
    
    return band_rescaled.astype(np.uint8)


def combine_rgb_layers(output_path, scl_mosaic):
    """
    Combines the red, green, and blue mosaic bands into a single multi-band raster and saves it.
    Uses the provided SCL mosaic to exclude cloud pixels during the rescaling process.
    
    Parameters:
        output_path (str): The directory where the mosaic raster files are located.
        scl_mosaic (rioxarray.DataArray): The mosaic SCL band used for cloud masking.
    """
    # Open each mosaic band.
    red = rioxarray.open_rasterio(f"{output_path}/red_mosaic.tif", chunks={"x": 1024, "y": 1024})
    green = rioxarray.open_rasterio(f"{output_path}/green_mosaic.tif", chunks={"x": 1024, "y": 1024})
    blue = rioxarray.open_rasterio(f"{output_path}/blue_mosaic.tif", chunks={"x": 1024, "y": 1024})


    # Ensure all bands are aligned
    red, green, blue = xr.align(red, green, blue)


    # Rescale each band to 0-255 using the provided SCL mosaic for masking.
    red = rescale_band(red, scl_mosaic)
    green = rescale_band(green, scl_mosaic)
    blue = rescale_band(blue, scl_mosaic)

    # Stack the rescaled bands into a single multi-band raster.
    rgb_mosaic = xr.concat([red, green, blue], dim="band")
    
    # Set the NoData value explicitly for all bands.
    rgb_mosaic.rio.write_nodata(0, inplace=True)
    
    # Save the RGB mosaic.
    save_raster(rgb_mosaic, "RGB", "mosaic", output_path)
    
def add_overviews(raster_path, overview_factors=[2, 4, 8, 16, 32], resampling_method=Resampling.average):
    """
    Adds overviews (pyramids) to an existing raster for faster rendering in web applications.
    
    Parameters:
    raster_path (str): Path to the raster file.
    overview_factors (list): List of overview levels (default: [2, 4, 8, 16, 32]).
    resampling_method (rasterio.enums.Resampling): Resampling method for overviews (default: average).
    """
    with rasterio.open(raster_path, 'r+') as src:
        # Build overviews at specified factors
        src.build_overviews(overview_factors, resampling_method)
        
        # Update tags to record overview information
        src.update_tags(ns='rio_overview', resampling=resampling_method.name)
    
    print(f"Overviews added to {raster_path} using {resampling_method.name} resampling.")
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
        red_band.close()
        del red_band
        
        blue_band = clip_band(scene.assets['blue'].href, geometry_utm)
        save_raster(blue_band, 'blue', scene.id, output_path)
        blue_band.close()
        del blue_band
        
        green_band = clip_band(scene.assets['green'].href, geometry_utm)
        save_raster(green_band, 'green', scene.id, output_path)
        green_band.close()
        del green_band
        
        scl_band = clip_band(scene.assets['scl'].href, geometry_utm)
        save_raster(scl_band, 'SCL', scene.id, output_path)
        scl_band.close()
        del scl_band
        
        red_band_masked, nir_band_masked = clip_and_mask_bands(scene, geometry_utm)
        
        ndvi = compute_ndvi(red_band_masked, nir_band_masked)
        ndvi = ndvi.rio.clip(geometry_utm.geometry.tolist(), crs=geometry_utm.crs)
        
        save_raster(ndvi, 'NDVI', scene.id, output_path)
        
        red_band_masked.close()
        nir_band_masked.close()
        ndvi.close()
        del red_band_masked, nir_band_masked, ndvi  # Delete the bands to free memory

    # After all scenes are processed, create a mosaic
    create_mosaic("NDVI", output_path, target_crs="EPSG:3857")
    # Changes final mosaic to Web Mercator
    create_mosaic("red", output_path, target_crs="EPSG:3857")
    create_mosaic("green", output_path, target_crs="EPSG:3857")
    create_mosaic("blue", output_path, target_crs="EPSG:3857")
    create_mosaic("SCL", output_path, target_crs="EPSG:3857")

    scl_mosaic = rioxarray.open_rasterio(f"{output_path}/SCL_mosaic.tif", chunks={"x": 1024, "y": 1024})
    combine_rgb_layers(output_path, scl_mosaic)
    
    add_overviews(f"{output_path}/RGB_mosaic.tif")
    add_overviews(f"{output_path}/NDVI_mosaic.tif")
    add_overviews(f"{output_path}/SCL_mosaic.tif")
    
    # Upload the RGB and NDVI mosaics to S3
    # client, BUCKET_NAME = connect_s3_client()
    # upload_image_to_s3(client, BUCKET_NAME, f"{output_path}/RGB_mosaic.tif", date_str)
    # upload_image_to_s3(client, BUCKET_NAME, f"{output_path}/NDVI_mosaic.tif", date_str)
    
def main():
    # 1. Set up environment & geometry
    working_directory = "/Volumes/Drew_ext_drive/NDVI_Proj"
    setup_environment(working_directory)
    
    geometry, geometry_utm = load_county_geometry('063')
    
    # 2. Initialize STAC client
    api_url = "https://earth-search.aws.element84.com/v1"
    client = Client.open(api_url)
    
    collection = "sentinel-2-l2a"
    
    # 3. Specify the target dates
    start_date = datetime(2024, 4, 1) # April 1, 2024
    end_date = datetime(2024, 6, 30) # June 31, 2024
    delta = timedelta(days=1)

    # # Include all dates from April-October 2024
    dates = [(start_date + delta * i).strftime("%Y-%m-%d") for i in range((end_date - start_date).days + 1)]
    # dates = ['2024-06-09']
    
    # 4. Process each date
    for date_str in dates:
        process_date(date_str, geometry, geometry_utm, collection, client)
        
main()

