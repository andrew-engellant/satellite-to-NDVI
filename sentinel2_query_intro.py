import requests

# Replace with your EROS credentials
username = "ae158765"
password = "Ace0324201!@"

auth_url = "https://espa.cr.usgs.gov/api"
response = requests.post(auth_url, json={"username": username, "password": password})

if response.status_code == 200:
    token = response.json()["token"]
    print("Authentication successful!")
else:
    print("Authentication failed:", response.text)

print(response.status_code)


from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt

api = SentinelAPI(username, password)
footprint = geojson_to_wkt(read_geojson('search_polygon.geojson'))
products = api.query(footprint,
                     producttype='SLC',
                     orbitdirection='ASCENDING',
                     limit=10)
api.download_all(products)





## AWS Sentinel-2 Collection 2A Intro
from pystac_client import Client
from shapely.geometry import Point, Polygon
import rioxarray
import geopandas as gpd
import matplotlib

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

