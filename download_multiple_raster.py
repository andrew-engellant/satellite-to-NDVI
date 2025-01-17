from pystac_client import Client
import rioxarray.merge
from shapely.geometry import Polygon
import rioxarray
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Load missoula county geometry
mso_county_box = Polygon([
    (-114.9, 46.6),  # Lower left
    (-113.5, 46.6),  # Lower right
    (-113.5, 47.7),  # Upper right
    (-114.9, 47.7),  # Upper left
    (-114.9, 46.6)  # Back to lower left to close the polygon
])

 # Initialize the client
api_url = "https://earth-search.aws.element84.com/v1"
client = Client.open(api_url)

collection = "sentinel-2-l2a"  # Sentinel-2, Level 2A, Cloud Optimized GeoTiffs (COGs)

search = client.search(
    collections=[collection], 
    bbox = mso_county_box.bounds, # Limits query to the bounding box of the MSO county
    datetime="2024-07-06", # TODO: Update the date range, # TODO: Update the number of items to return
    query={"eo:cloud_cover": {"lt": 10}}, # Limits query to images with less than 10% cloud cover
)

search.matched() # Check for how many scenes match our search criteria
# 2 Scenes matched
items = search.item_collection()

# Convert mso_county_box to a GeoDataFrame for clipping
mso_county_gdf = gpd.GeoDataFrame({'geometry': [mso_county_box]}, crs="EPSG:4326")
mso_county_geojson = mapping(mso_county_box)  # Convert the polygon to GeoJSON format

rasters = [] # Create an empty list to store the rasters
for scene in items:
    print(f"ID: {scene.id}")
    print(f"Date: {scene.datetime}")
    print(f"Cloud Cover: {scene.properties['eo:cloud_cover']}")
    
    assets = scene.assets # Access the assets for the scene
    
    # Load the Red band
    red_band_url = assets['red'].href # Grab URL for the red band
    red_band = rioxarray.open_rasterio(red_band_url) # Open the raster

    # Crop the Red band to the MSO county box
    red_band = red_band.rio.clip([mso_county_geojson], crs="EPSG:4326") 
    
    # Load the NIR band
    nir_band_url = assets['nir'].href # Grab URL for the nir band
    nir_band = rioxarray.open_rasterio(nir_band_url)    
    
    # Crop the NIR band to the MSO county box
    nir_band = nir_band.rio.clip([mso_county_geojson], crs="EPSG:4326")
    
    # Ensure the two rasters align
    red_band, nir_band = xr.align(red_band, nir_band)
    
    # Calculate NDVI
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    
    # Add metadata to the NDVI raster
    ndvi = ndvi.rio.write_crs(red_band.rio.crs, inplace=True)
    ndvi.attrs['long_name'] = 'Normalized Difference Vegetation Index (NDVI)'
    ndvi.attrs['units'] = 'None'
    
    # Add the NDVI raster to the list
    rasters.append(ndvi)
    
    

merged_raster = rioxarray.merge.merge_arrays(rasters)
# Write CRS explicitly (if not already set)
merged_raster = merged_raster.rio.write_crs(rasters[0].rio.crs)

# Reproject to EPSG:4326
merged_reprojected = merged_raster.rio.reproject("EPSG:4326")

# Save the reprojected raster
# merged_reprojected.rio.to_raster("raster_images/merged_reprojected.tif")

# Plot the reprojected raster with cartopy
fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": ccrs.PlateCarree()})
merged_reprojected.plot(ax=ax, robust=True, transform=ccrs.PlateCarree())

# Add gridlines and labels
gl = ax.gridlines(draw_labels=True, crs=ccrs.PlateCarree(), alpha=0.5)
gl.top_labels = False
gl.right_labels = False

# Add a title and show the plot
ax.set_title("Reprojected Mosaic with Geographical Context")
plt.show()
