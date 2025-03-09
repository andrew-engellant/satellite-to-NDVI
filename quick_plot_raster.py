""" 
This script is used as a tool to quickly visualize download raster images to aid in the debugging process.
This script is not a part of the main application and is used for testing purposes only.
"""

import rasterio
import matplotlib.pyplot as plt
import numpy as np

from rasterio.io import MemoryFile
from upload_to_DO import connect_s3_client

# Function to apply a percentile-based contrast stretch
def contrast_stretch(band, lower_percentile=2, upper_percentile=98):
    # Calculate the percentiles
    lower = np.percentile(band, lower_percentile)
    upper = np.percentile(band, upper_percentile)

    # Clip the band to the percentiles and normalize to [0, 1]
    band_stretched = np.clip(band, lower, upper)
    band_stretched = (band_stretched - lower) / (upper - lower)
    return band_stretched


# Plot RGB raster
raster_path = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/April/10/RGB_mosaic.tif'
with rasterio.open(raster_path) as src:
    # Read the red, green, and blue bands (assuming bands 1, 2, and 3)
    red = src.read(1)
    green = src.read(2)
    blue = src.read(3)

    # Stack the bands into a single RGB array
    rgb = np.dstack((red, green, blue))

    # Apply contrast stretch to each band
    red_stretched = contrast_stretch(red)
    green_stretched = contrast_stretch(green)
    blue_stretched = contrast_stretch(blue)

    # Stack the stretched bands into a single RGB array
    rgb_stretched = np.dstack((red_stretched, green_stretched, blue_stretched))

    # Plot the RGB image with improved contrast
    plt.figure(figsize=(9, 9))
    plt.imshow(rgb_stretched)
    plt.axis('off')  # Hide the axis
    plt.title('RGB Image with Contrast Stretch')
    plt.show()


# Plot NDVI raster
ndvi_raster_path = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/July/01/red_mosaic.tif'
with rasterio.open(ndvi_raster_path) as src:
    # Read the NDVI band (assuming it's the first band)
    ndvi = src.read(1)

    # Replace 0 values with NaN
    ndvi = np.where(ndvi == 0, np.nan, ndvi)

    # Mask out NoData values (if any)
    ndvi = np.ma.masked_where(np.isnan(ndvi), ndvi)

    # Plot the NDVI raster with a colormap
    plt.figure(figsize=(10, 10))
    # Use a red-yellow-green colormap
    ndvi_plot = plt.imshow(ndvi, cmap='RdYlGn')

    # Add a colorbar
    cbar = plt.colorbar(ndvi_plot, fraction=0.046, pad=0.04)
    cbar.set_label('NDVI')

    # Add a title and hide the axis
    plt.title('NDVI Raster')
    plt.axis('off')

    # Show the plot
    plt.show()

OBJECT_KEY = "montana/2024/07/26/RGB-missoula-2024-07-26.tif"

s3_client, BUCKET_NAME = connect_s3_client()
response = s3_client.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
file_data = response["Body"].read()  # Read file into memory

# Read the raster data using rasterio's MemoryFile
with MemoryFile(file_data) as memfile:
    with memfile.open() as src:
        # Read the red, green, and blue bands (assuming bands 1, 2, and 3)
        red = src.read(1)
        green = src.read(2)
        blue = src.read(3)

        # Apply contrast stretching
        red_stretched = contrast_stretch(red)
        green_stretched = contrast_stretch(green)
        blue_stretched = contrast_stretch(blue)

        # Stack the stretched bands into a single RGB array
        rgb_stretched = np.dstack(
            (red_stretched, green_stretched, blue_stretched))

        # Plot the RGB image with improved contrast
        plt.figure(figsize=(10, 10))
        plt.imshow(rgb_stretched)
        plt.axis('off')  # Hide the axis
        plt.title('RGB Image with Contrast Stretch')
        plt.show()

ndvi_raster_path = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/April/22/RGB_mosaic.tif'
with rasterio.open(ndvi_raster_path) as src:
    # Read the NDVI raster data
    ndvi_data = src.read(1)
    # View the most common values
    print(np.unique(ndvi_data, return_counts=True))

# Changing nan values to -9999
with rasterio.open(ndvi_raster_path, "r+") as src:
    ndvi = src.read(1)

    # Replace -9999 with NaN
    ndvi[ndvi == -9999] = np.nan

    # Update NoData value in metadata
    src.nodata = np.nan

    # Write back the modified data
    src.write(ndvi, 1)
