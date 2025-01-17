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

rasters = [] # Create an empty list to store the rasters
for scene in items:
    print(f"ID: {scene.id}")
    print(f"Date: {scene.datetime}")
    print(f"Cloud Cover: {scene.properties['eo:cloud_cover']}")
    assets = scene.assets # Access the assets for the scene
    red_band_url = assets['red'].href # Grab URL for the red band
    rasters.append(rioxarray.open_rasterio(red_band_url)) # Open the raster
    
    #TODO: # Add code to download the nir band

merged_raster = rioxarray.merge.merge_arrays(rasters)

merged_reprojected = merged_raster.rio.reproject("EPSG:4326")

# Plot the reprojected raster with cartopy
fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": ccrs.PlateCarree()})
merged_reprojected.plot(ax=ax, robust=True, cmap="Reds", transform=ccrs.PlateCarree())

# Add gridlines and labels
gl = ax.gridlines(draw_labels=True, crs=ccrs.PlateCarree(), alpha=0.5)
gl.top_labels = False
gl.right_labels = False

# Add a title and show the plot
ax.set_title("Reprojected Mosaic with Geographical Context")
plt.show()
