## AWS Sentinel-2 Collection 2A Intro
from pystac_client import Client
from shapely.geometry import Point
import rioxarray
import geopandas as gpd

api_url = "https://earth-search.aws.element84.com/v1"

 # Initialize the client
client = Client.open(api_url)

collection = "sentinel-2-l2a"  # Sentinel-2, Level 2A, Cloud Optimized GeoTiffs (COGs)

point = Point(113.99, 46.87) #Missoula, MT

search = client.search(
    collections=[collection],
    intersects=point,
    max_items=4,
)

print(search.matched()) # Check for how many scenes match our search criteria

items = search.item_collection() # Retreive the items
print(len(items))

for item in items:
    print(item)
    
# Let's look at the first item
item = items[0]
print(item.datetime)
print(item.geometry)
print(item.properties)

# To access the image, we need to get the item's assets
assets = items[0].assets # Looks at the assests for the first item
print(assets.keys())

# QUick description of each availible band
for key, asset in assets.items():
    print(f"{key}: {asset.title}")
    
print(assets["thumbnail"].href)

nir_href = assets["nir"].href
nir = rioxarray.open_rasterio(nir_href)
print(nir)

red_href = assets["red"].href
red = rioxarray.open_rasterio(red_href)
print(red)

