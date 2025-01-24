from pystac_client import Client
import rioxarray.merge
from shapely.geometry import Polygon
import rioxarray
from rioxarray.merge import merge_arrays
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from shapely.geometry import mapping
import geopandas as gpd
import datetime as dt
import glob
import os
import numpy as np

os.chdir("/Volumes/Drew_ext_drive/NDVI_Proj") # Set directory to save rasters

# Load missoula county geometry
mso_county_box = Polygon([
    (-114.9, 46.6),  # Lower left
    (-113.5, 46.6),  # Lower right
    (-113.5, 47.7),  # Upper right
    (-114.9, 47.7),  # Upper left
    (-114.9, 46.6)  # Back to lower left to close the polygon
])

mso_county_gdf = gpd.GeoDataFrame({'geometry': [mso_county_box]}, crs="EPSG:4326")
mso_county_geojason_latlong = mapping(mso_county_gdf.geometry[0])
mso_county_gdf = mso_county_gdf.to_crs("EPSG:32611")  # Reproject to UTM Zone 11
mso_county_geojson_UTM = mapping(mso_county_gdf.geometry[0])

 # Initialize the client
api_url = "https://earth-search.aws.element84.com/v1"
client = Client.open(api_url)

collection = "sentinel-2-l2a"  # Sentinel-2, Level 2A, Cloud Optimized GeoTiffs (COGs)


def clip_band(band_url, clip_geometry, target_crs="EPSG:32611"):
    band = rioxarray.open_rasterio(band_url, chunks={"x": 1024, "y": 1024}) # Chunks attribute speeds up processing
    
    if band.rio.crs != target_crs:
        band = band.rio.reproject(target_crs) # Ensure the raster is projected to UTM zone 11
        
    band = band.rio.clip([clip_geometry], crs=target_crs)
    return band # Returns the clipped raster

def get_vegitation_pixils(target_band, scl_band, clip_geometry, target_crs="EPSG:32611"):
    
    if scl_band.rio.crs != target_crs:
        scl_band = scl_band.rio.reproject(target_crs)
    
    scl_band = scl_band.rio.clip([clip_geometry], crs=target_crs)
    
    scl_resampled = scl_band.rio.reproject_match(target_band) # Since the scl band is lower resolution, we need to resample it to match the red band
    vegitation_values_aligned = scl_resampled == 4 # Create a mask for vegitation values
    band_masked = target_band.where(vegitation_values_aligned) # Apply the mask to the band
    
    return band_masked


def create_mosaic(band_name, output_path, target_crs="EPSG:32611"):
    # Gather all raster files for the specific band
    band_files = glob.glob(f"{output_path}/{band_name}_*.tif")
    
    # Open all the rasters into a list
    raster_list = [rioxarray.open_rasterio(file, chunks={"x": 1024, "y": 1024}) for file in band_files]
    
    # Merge the rasters
    mosaic = merge_arrays(raster_list)
    
    # Compute the mosaic to load it into memory
    mosaic = mosaic.compute()

    # Reproject the mosaic to ensure CRS consistency
    mosaic = mosaic.rio.reproject(target_crs)
    
    # Save the final mosaic
    mosaic.rio.to_raster(
    f"{output_path}/NDVI_merged.tif",
    driver="GTiff", # Ensures the output is a GeoTIFF
    compress="LZW", 
    tiled=True, # Allows for reading/writing in smaller chunks
    blockxsize=256,
    blockysize=256
)
    print(f"{band_name} mosaic saved to {output_path}")
    
# TODO: Loop through multiple dates and create NDVI rasters   
dates = ["2024-07-26"] 
for date in dates:
    search = client.search(
        collections=[collection],
        intersects=mso_county_geojason_latlong,
        datetime=str(date)
    )
    
    if search.matched() > 0: # If no scenes are found, skip to the next date
        items = search.item_collection()
        print(f"{len(items)} Scenes matched for {date}")
        
        date_obj = dt.datetime.strptime(date, "%Y-%m-%d")
        month = date_obj.strftime("%B")
        day = date_obj.strftime("%d")
        
        output_path = f"rasters/historic_NDVI_rasters/2024/{month}/{day}" 
        os.makedirs(output_path, exist_ok=True) # Create a new directory for the date
        
        for scene in items:
            print(f"Processing scene ID: {scene.id}")
            assets = scene.assets
            
            # Load and process red and nir bands
            red_band = clip_band(assets['red'].href, mso_county_geojson_UTM)
            nir_band = clip_band(assets['nir'].href, mso_county_geojson_UTM)
            
            # Load SCL band
            scl_band = rioxarray.open_rasterio(assets['scl'].href, chunks={"x": 1024, "y": 1024})
            
            red_band_masked = get_vegitation_pixils(red_band, scl_band, mso_county_geojson_UTM)
            nir_band_masked = get_vegitation_pixils(nir_band, scl_band, mso_county_geojson_UTM)
            
            # Make sure RED and NIR bands align
            red_band_masked, nir_band_masked = xr.align(red_band_masked, nir_band_masked)
            
            ndvi = xr.where(
                ~xr.ufuncs.isnan(nir_band_masked) & ~xr.ufuncs.isnan(red_band_masked),
                xr.where(
                    (nir_band_masked + red_band_masked) > 0,
                    (nir_band_masked - red_band_masked) / (nir_band_masked + red_band_masked),
                    0  # Assign 0 where the denominator is 0
                ),
                np.nan  # Assign NaN if either NIR or Red is NaN
            )
            
            ndvi = ndvi.rio.write_crs(red_band_masked.rio.crs) # Ensure the NDVI raster has a CRS
            
            # Save individual NDVI raster
            output_file = f"{output_path}/NDVI_{scene.id}.tif"
            ndvi.rio.to_raster(output_file)
            print(f"Saved NDVI raster to {output_file}")
                
        
        create_mosaic("NDVI", output_path) 
        