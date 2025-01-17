from pystac_client import Client
import rioxarray.merge
from shapely.geometry import Polygon
import rioxarray
import xarray as xr
import rasterio.merge as merge
import rasterio
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
items = search.get_all_items()
for scene in items:
    print(scene.id, scene.datetime, scene.properties["eo:cloud_cover"])
    name = scene.id
    assets = scene.assets # Access the assets for the scene
    band = assets['red'].href # Grab URL for the red band
    raster = rioxarray.open_rasterio(band) # Open the raster
    raster.rio.to_raster(f"raster_images/{name}_red.tif") # Save the raster to disk
    
    TODO: # Add code to download the nir band
        
raster1 = rasterio.open("raster_images/S2A_11TPM_20240706_0_L2A_red.tif")
raster2 = rasterio.open("raster_images/S2A_11TQM_20240706_0_L2A_red.tif")

mosaic, transform = rasterio.merge.merge([raster1, raster2]) # Merge together each raster

out_meta = raster1.meta.copy() # Copies the meta-data from the first raster
out_meta.update({               # Updates the meta-data with the new dimensions matching the merged raster
    "driver": "GTiff",
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": transform      # Updates the transform to match the merged raster
})
with rasterio.open("raster_images/merged_red.tif", "w", **out_meta) as dest:
    dest.write(mosaic)

mosaic_riox = rioxarray.open_rasterio("raster_images/merged_red.tif") # Open the merged raster
mosaic_reprojected = mosaic_riox.rio.reproject("EPSG:4326") # Reproject the merged raster to WGS84

# Plot the reprojected mosaic
fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": ccrs.PlateCarree()})
mosaic_reprojected.plot(ax=ax, robust=True, cmap="Reds", transform=ccrs.PlateCarree())

# Add gridlines and labels for longitude/latitude
gl = ax.gridlines(draw_labels=True, crs=ccrs.PlateCarree(), alpha=0.5)
gl.top_labels = False
gl.right_labels = False

# Add a title and show the plot
ax.set_title("Reprojected Mosaic with Geographical Context")
plt.show()


# Plot the merged raster
plt.figure(figsize=(10, 10))
plt.imshow(mosaic_reprojected[0])  # Display the first band of the merged raster
plt.colorbar(label="Reflectance")
plt.title("Merged Raster Visualization")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.show()