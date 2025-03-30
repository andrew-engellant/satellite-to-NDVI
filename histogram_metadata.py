"""
This script processes NDVI mosaic raster files to generate histogram data and statistics for each day of the year 2024. 
The histogram data includes the counts and bins for a range of NDVI values, as well as the median and mean NDVI values. 
This data is then saved to pickle files, which are used in a web application to quickly render histogram visualizations 
for each day, providing insights into vegetation health over time.
"""

base_dir = "/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024"

import pickle
import numpy as np
import os
import rasterio
from pathlib import Path

for month in os.listdir(base_dir):
    if month == ".DS_Store":
        continue
    else:
        print("working on month:", month)
        for day in os.listdir(f"{base_dir}/{month}"):
            if day == ".DS_Store":
                continue
            else:
                output_path = f"{base_dir}/{month}/{day}"
                with rasterio.open(f"{output_path}/NDVI_mosaic.tif") as src:
                    ndvi_data = src.read(1)
                    valid_data = ndvi_data[~np.isnan(ndvi_data)]
                    
                    # Create histogram data
                    hist_range = (0.2, 1)
                    hist_bins = 25
                    hist_counts, hist_bins = np.histogram(valid_data, bins=hist_bins, range=hist_range)
                    
                    # Calculate median
                    median_ndvi = np.nanmedian(ndvi_data)
                    mean_ndvi = np.nanmean(ndvi_data)
                    
                    # Package histogram data and statistics
                    histogram_data = {
                        'counts': hist_counts,
                        'bins': hist_bins,
                        'median': median_ndvi,
                        'mean': mean_ndvi,
                        'date': f"{month}-{day}"
                    }
                    
                    # Save histogram data to pickle file
                    pickle_filename = f"{output_path}_hist.pkl"
                    with open(pickle_filename, 'wb') as f:
                        pickle.dump(histogram_data, f)
                    
                    print(f"Saved histogram data to {pickle_filename}")
                    
                    
# date_str = "2024-07-26"
output_path = "/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/April/17"