import rasterio
import matplotlib.pyplot as plt
import numpy as np

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
raster_path = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/July/26/RGB_mosaic.tif'
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
    plt.figure(figsize=(10, 10))
    plt.imshow(rgb_stretched)
    plt.axis('off')  # Hide the axis
    plt.title('RGB Image with Contrast Stretch')
    plt.show()
    

# Plot NDVI raster
ndvi_raster_path = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/July/26/NDVI_merged_mosaic.tif'
with rasterio.open(ndvi_raster_path) as src:
    # Read the NDVI band (assuming it's the first band)
    ndvi = src.read(1)

        # Replace 0 values with NaN
    ndvi = np.where(ndvi == 0, np.nan, ndvi)

    # Mask out NoData values (if any)
    ndvi = np.ma.masked_where(np.isnan(ndvi), ndvi)

    # Plot the NDVI raster with a colormap
    plt.figure(figsize=(10, 10))
    ndvi_plot = plt.imshow(ndvi, cmap='RdYlGn', vmin=0.2, vmax=1)  # Use a red-yellow-green colormap

    # Add a colorbar
    cbar = plt.colorbar(ndvi_plot, fraction=0.046, pad=0.04)
    cbar.set_label('NDVI')

    # Add a title and hide the axis
    plt.title('NDVI Raster')
    plt.axis('off')

    # Show the plot
    plt.show()