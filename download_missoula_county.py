from pystac_client import Client
from shapely.geometry import Point, Polygon
import rioxarray
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import mapping

shapefile_path = "/Users/drewengellant/Documents/MSBA/Spring25/capstone/satellite-to-NDVI/shapefiles/missoula_county"

# Path to your Shapefile
shapefile_path = "/Users/drewengellant/Documents/MSBA/Spring25/capstone/satellite-to-NDVI/shapefiles/missoula_county"

# Read the Shapefile
gdf = gpd.read_file(shapefile_path)

gdf.head()
    

# Plot the data
gdf.plot()
plt.title("Missoula County Map")
plt.show()

# MSO County max lat/long = 47.7, -113.5
# MSO County min lat/long = 46.6, -114.9
# Create a polygon shape that forms a box around the MSO county
mso_county_box = Polygon([
    (-114.9, 46.6),  # Lower left
    (-113.5, 46.6),  # Lower right
    (-113.5, 47.7),  # Upper right
    (-114.9, 47.7),  # Upper left
    (-114.9, 46.6)  # Back to lower left to close the polygon
])


api_url = "https://earth-search.aws.element84.com/v1"

 # Initialize the client
client = Client.open(api_url)

collection = "sentinel-2-l2a"  # Sentinel-2, Level 2A, Cloud Optimized GeoTiffs (COGs)

search = client.search(
    collections=[collection], 
    bbox = mso_county_box.bounds, # Limits query to the bounding box of the MSO county
    datetime="2024-07-01/2024-07-15", # TODO: Update the date range
    max_items=4, # TODO: Update the number of items to return
    query={"eo:cloud_cover": {"lt": 10}}, # Limits query to images with less than 10% cloud cover
)

print(search.matched()) # Check for how many scenes match our search criteria

items = search.item_collection() # Retreive the items
print(len(items))

for item in items:
    print(item)
    
# Let's look at the first item
item = items[1]
print(item.datetime)
print(item.geometry)
print(item.properties)



# To access the image, we need to get the item's assets
assets = items[1].assets # Looks at the assests for the first item
print(assets.keys())

print(assets["thumbnail"].href) # Prints the thumbnail image


# Raster data can be opened using the rioxarray library
# Let's open the red band
red_href = assets["red"].href
red = rioxarray.open_rasterio(red_href)
print(red)

# save portion of an image to disk
red[0,1500:2200,1500:2200].rio.to_raster("red_subset.tif")

# Load a .tif file using rioxarray
image_path = "raster_images/red_subset.tif"
red_raster = rioxarray.open_rasterio(image_path)

print(red_raster.rio.crs.to_epsg()) # Check the CRS
print(red_raster.rio.nodata)
print(red_raster.rio.bounds())
print(red_raster.rio.width)
print(red_raster.rio.height)

red_raster.plot(robust=True)
plt.show()

# Reproject the raster to EPSG:4326 (longitude, latitude)
red_raster_geo = red_raster.rio.reproject("EPSG:4326")

# Plot the reprojected raster
red_raster_geo.plot(robust=True)
plt.title("Raster Aligned with Longitude and Latitude")
plt.show()

