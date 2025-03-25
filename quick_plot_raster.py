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

### Code for producing a histogram of NDVI distribution
ndvi_raster_path = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/April/22/NDVI_mosaic.tif'
with rasterio.open(ndvi_raster_path) as src:
    ndvi_data = src.read(1)
    plt.hist(ndvi_data[~np.isnan(ndvi_data)], bins=20, alpha=0.5, label='NDVI Values', range=(0.2, 1))
    plt.title('Histogram of NDVI Values')
    plt.xlabel('NDVI Value')
    plt.ylabel('Frequency')
    plt.legend()
    
    # Calculate and plot the median
    median_ndvi = np.nanmedian(ndvi_data)
    plt.axvline(x=median_ndvi, color='red', linestyle='-', label=f'Median: {median_ndvi:.2f}')
    plt.legend()
    
    plt.show()

### Code for producing a timeseries plot of NDVI values
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from scipy.signal import savgol_filter

# Load the DataFrame
ndvi_data = pd.read_csv('/Users/drewengellant/Documents/MSBA/Spring25/capstone/satellite-to-NDVI/ndvi_data.csv')
# Convert date column to datetime
ndvi_data['date'] = pd.to_datetime(ndvi_data['date'])

# Apply the filtering conditions
filtered_df = ndvi_data[(ndvi_data['cloud_cover_pct'] <= 50) & (ndvi_data['total_pixels'] >= 50000000)]

# Sort by date for proper time series plotting
filtered_df = filtered_df.sort_values('date')

# Apply a Savitzky-Golay filter for smoothing
smoothed_ndvi = savgol_filter(filtered_df['median_ndvi'], window_length=7, polyorder=3, mode='nearest')

# Plot the original data and the smoothed trend
plt.figure(figsize=(12, 6))
plt.scatter(filtered_df['date'], filtered_df['median_ndvi'], marker='o', label='Raw NDVI')
plt.plot(filtered_df['date'], smoothed_ndvi, linestyle='-', linewidth=2, label='Smoothed Trend', color='red')

# Formatting
plt.title('Median NDVI Over Time (With Smoothing)')
plt.ylabel('Median NDVI')
plt.legend()
plt.grid(False)
plt.xticks()
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%B'))
plt.show()


### Code for producing a timeseries plot of Veg % 
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import matplotlib.dates as mdates
from scipy.signal import savgol_filter

# Load the DataFrame
ndvi_data = pd.read_csv('/Users/drewengellant/Documents/MSBA/Spring25/capstone/satellite-to-NDVI/ndvi_data.csv')
# Convert date column to datetime
ndvi_data['date'] = pd.to_datetime(ndvi_data['date'])

# Apply the filtering conditions
filtered_df = ndvi_data[(ndvi_data['cloud_cover_pct'] <= 50) & (ndvi_data['total_pixels'] >= 50000000)]

# Sort by date for proper time series plotting
filtered_df = filtered_df.sort_values('date')

# Apply a Savitzky-Golay filter for smoothing
smoothed_ndvi = savgol_filter(filtered_df['veg_abundance_pct'], window_length=7, polyorder=3, mode='nearest')

# Fix the x-axis to show only one label per month
plt.figure(figsize=(12, 6))
plt.scatter(filtered_df['date'], filtered_df['veg_abundance_pct'], marker='o', label='Raw NDVI')
plt.plot(filtered_df['date'], smoothed_ndvi, linestyle='-', linewidth=2, label='Smoothed Trend', color='red')

# Formatting
plt.title('Vegetation Abundance Over Time')
plt.ylabel('Percentage of Vegetation Coverage')
plt.legend()
plt.grid(False)

# Set major locator to use months as tick positions
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
# Format the dates to show month names
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%B'))

# Optionally, if your data spans multiple years, include the year in the label
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%B %Y'))

# If you have many months, you might want to rotate the labels for better readability
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()


data = pd.read_csv('/Users/drewengellant/Documents/MSBA/Spring25/capstone/satellite-to-NDVI/ndvi_data.csv')
# Plotting a histogram of the average NDVI column
plt.figure(figsize=(10, 6))
plt.hist(data['var_coeff_ndvi'], bins=30, alpha=0.7, color='blue', edgecolor='black')
plt.title('Histogram of Average NDVI')
plt.xlabel('Average NDVI')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()

