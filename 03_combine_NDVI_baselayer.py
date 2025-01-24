import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from rasterio.plot import show
import os

os.chdir("/Volumes/Drew_ext_drive/NDVI_Proj") 

def normalize_with_percentiles(band, lower_percentile=2, upper_percentile=98):
    return (band - np.nanpercentile(band, lower_percentile)) / (np.nanpercentile(band, upper_percentile) - np.nanpercentile(band, lower_percentile))

# 1. Open the base RGB raster
with rasterio.open("rasters/base_layer_full_color/final_rgb_mosaic.tif") as src_rgb:
    rgb_data = src_rgb.read()  # shape: (3, height, width)
    rgb_data = normalize_with_percentiles(rgb_data, 2, 98)  # TODO: Add in funcionality to only include 2-98 percentiles
    rgb_transform = src_rgb.transform
    rgb_crs = src_rgb.crs
    

# 2. Open the NDVI raster
with rasterio.open("rasters/historic_NDVI_rasters/2024/July/26/NDVI_merged.tif") as src_ndvi:
    ndvi_data = src_ndvi.read(1)  # shape: (height, width)
    ndvi_transform = src_ndvi.transform
    ndvi_crs = src_ndvi.crs

ndvi_hist = np.histogram(ndvi_data, bins=100, range=(0,1))
plt.plot(ndvi_hist[1][:-1], ndvi_hist[0], color='r')
plt.title('NDVI Histogram')
plt.show()

fig, ax = plt.subplots(figsize=(10, 10))


show(
    rgb_data,           
    transform=rgb_transform,
    ax=ax
)

show(
    ndvi_data,
    transform=ndvi_transform,
    ax=ax,
    alpha=0.2,          # transparency
    cmap='RdYlGn',     
    vmin=0.3,           # set minimum value for color scaling
    vmax=1              # set maximum value for color scaling
)


plt.title("NDVI overlay on RGB base layer")
plt.show()