from pystac_client import Client
import rioxarray.merge
from shapely.geometry import Polygon
import rioxarray
import glob
from rioxarray.merge import merge_arrays
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from shapely.geometry import mapping
import geopandas as gpd
import datetime as dt
import os

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
mso_county_gdf = mso_county_gdf.to_crs("EPSG:32611")  # Reproject to UTM Zone 11
mso_county_geojson = mapping(mso_county_gdf.geometry[0])  # Convert to GeoJSON format


 # Initialize the client
api_url = "https://earth-search.aws.element84.com/v1"
client = Client.open(api_url)

# Now that the client is initialized, we can search for sunny scenes to use as the base layer
# Let's start by looking through july and find the day with the least cloud cover

collection = "sentinel-2-l2a"  # Sentinel-2, Level 2A, Cloud Optimized GeoTiffs (COGs)
# dates = [dt.datetime(2024, 7, i) for i in range(1, 32)] # Create a list of dates for July 2024
# dates = [date.strftime("%Y-%m-%d") for date in dates] # Change format to YYYY-MM-DD

# for date in dates:
#     search = client.search(
#         collections=[collection],
#         intersects = mso_county_geojson, # Limits query to MSO county
#         datetime=str(date)
#     )
    
#     print(f"{search.matched()} Scenes matched for {date}")
#     if search.matched() > 0:
#         cloud_cover = []
#         for i in range(search.matched()):
#             item = search.item_collection()[i]
#             cloud_cover.append(item.properties['eo:cloud_cover'])
#         print(f"Average cloud cover is {sum(cloud_cover) / len(cloud_cover)}%")
#     print("\n")

# Looks like July 26th was a nice sunny day
search = client.search(
    collections=[collection],
    intersects = mso_county_geojson,
    datetime=str("2024-07-26") # Let's grab all the scenes from July 26th
)

items = search.item_collection()


# We want Red, Green, and Blue rasters to use as the base layer
def process_band(band_url, band_name, scene_id, clip_geometry, target_crs="EPSG:32611"):
    band = rioxarray.open_rasterio(band_url, chunks={"x": 1024, "y": 1024}) # Chunks attribute speeds up processing
    
    if band.rio.crs != target_crs:
        band = band.rio.reproject(target_crs) # Ensure the raster is projected to UTM zone 11
        
    band = band.rio.clip([clip_geometry], crs=target_crs) 
    output_path = f"rasters/base_layer_full_color/{band_name}_{scene_id}.tif"
    band.rio.to_raster(output_path)
    print(f"{band_name.capitalize()} band saved to {output_path}")

for scene in items:
    print(f"Working on scene {scene.id}...")
    
    assets = scene.assets
    process_band(assets['red'].href, 'red', scene.id, mso_county_geojson)
    process_band(assets['green'].href, 'green', scene.id, mso_county_geojson)
    process_band(assets['blue'].href, 'blue', scene.id, mso_county_geojson)
    


# Create a mosaic function
def create_mosaic(band_name, output_path, target_crs="EPSG:32611"):
    # Gather all raster files for the specific band
    band_files = glob.glob(f"rasters/base_layer_full_color/{band_name}_*.tif")
    
    # Open all the rasters into a list
    raster_list = [rioxarray.open_rasterio(file, chunks={"x": 1024, "y": 1024}) for file in band_files]
    
    # Merge the rasters
    mosaic = merge_arrays(raster_list)
    
    # Reproject the mosaic to ensure CRS consistency
    mosaic = mosaic.rio.reproject(target_crs)
    
    # Save the final mosaic
    mosaic.rio.to_raster(output_path, compress="LZW")
    print(f"{band_name.capitalize()} mosaic saved to {output_path}")

# Create mosaics for each band
create_mosaic("red", "rasters/base_layer_full_color/mosaic_red.tif")
create_mosaic("green", "rasters/base_layer_full_color/mosaic_green.tif")
create_mosaic("blue", "rasters/base_layer_full_color/mosaic_blue.tif")

# Combine the RGB mosaics into a single raster
def combine_rgb(red_path, green_path, blue_path, output_path):
    # Open each band
    red = rioxarray.open_rasterio(red_path, chunks={"x": 1024, "y": 1024})
    green = rioxarray.open_rasterio(green_path, chunks={"x": 1024, "y": 1024})
    blue = rioxarray.open_rasterio(blue_path, chunks={"x": 1024, "y": 1024})
    
    # Stack bands into a single multi-band raster
    rgb_mosaic = xr.concat([red, green, blue], dim="band")
    
    # Save the final RGB mosaic
    rgb_mosaic.rio.to_raster(output_path, compress="LZW")
    print(f"RGB mosaic saved to {output_path}")

# Create the final RGB mosaic
combine_rgb(
    "rasters/base_layer_full_color/mosaic_red.tif",
    "rasters/base_layer_full_color/mosaic_green.tif",
    "rasters/base_layer_full_color/mosaic_blue.tif",
    "rasters/base_layer_full_color/final_rgb_mosaic.tif"
)


# Plot the final RGB mosaic
rgb_mosaic = rioxarray.open_rasterio("rasters/base_layer_full_color/final_rgb_mosaic.tif")
rgb_mosaic = rgb_mosaic.transpose("y", "x", "band")  # Reorder dimensions for plotting
rgb_mosaic.plot.imshow(robust=True, figsize=(10, 10))
plt.show()








    
# # We want Red, Green, and Blue rasters to use as the base layer
# items = search.item_collection()
# for scene in items:
#     print(f"Working on scene {scene.id}...")
    
#     assets = scene.assets
    
#     # Load the Red band
#     red_band_url = assets['red'].href # Grab URL for the red band
#     red_band = rioxarray.open_rasterio(red_band_url, chunks={"x": 1024, "y": 1024}) # Chunks attribute speeds up processing
#     red_band = red_band.rio.reproject("EPSG:3857") # Ensure the raster is projected to ESPG 3857
#     red_band = red_band.rio.clip([mso_county_geojson], crs="EPSG:3857") # Crop the Red band to the MSO county box
#     red_band.rio.to_raster(f"rasters/base_layer/red_{scene.id}.tif") # Save the raster to disk
    
#     # Load the Green Band
#     green_band_url = assets['green'].href # Grab URL for the green band
#     green_band = rioxarray.open_rasterio(green_band_url, chunks={"x": 1024, "y": 1024}) 
#     green_band = green_band.rio.reproject("EPSG:3857")
#     green_band = green_band.rio.clip([mso_county_geojson], crs="EPSG:3857") 
#     green_band.rio.to_raster(f"rasters/base_layer/green_{scene.id}.tif") # Save the raster
 
#     # Load the Blue Band
#     blue_band_url = assets['blue'].href # Grab URL for the blue band
#     blue_band = rioxarray.open_rasterio(blue_band_url, chunks={"x": 1024, "y": 1024}) 
#     blue_band = blue_band.rio.reproject("EPSG:3857")
#     blue_band = blue_band.rio.clip([mso_county_geojson], crs="EPSG:3857") 
#     blue_band.rio.to_raster(f"rasters/base_layer/blue_{scene.id}.tif") # Save the raster
    
    
    
    