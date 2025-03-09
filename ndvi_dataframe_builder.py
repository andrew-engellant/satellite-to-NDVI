"""
This script processes NDVI (Normalized Difference Vegetation Index) data from historic raster files.
It reads NDVI and SCL (Scene Classification Layer) data for each day of specified months in 2024,
calculates various statistics (average, median, standard deviation, and variation coefficient) for the NDVI data,
and computes pixel counts for vegetation and cloud cover. The results are stored in a Pandas DataFrame,
which is then sorted by date and saved to a CSV file named 'ndvi_data.csv'.

The resulting dataframe will be implemented into the application to provide descriptive statistics for the NDVI data.
"""

import rioxarray
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Define column names with shortened, underscore-separated names
columns = [
    "date", "total_pixels", "veg_pixels", "masked_pixels",
    "cloud_cover_pct", "veg_abundance_pct", "avg_ndvi",
    "median_ndvi", "std_ndvi", "var_coeff_ndvi"
]
df = pd.DataFrame(columns=columns)

# Month-to-number mapping
month_num = {
    "April": "04", "May": "05", "June": "06", "July": "07",
    "August": "08", "September": "09", "October": "10"
}

# Process data for each month and day
# Add other months as needed
for month in ["April", "May", "June", "July", "August", "September", "October"]:
    for day in os.listdir(f"/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/{month}"):
        if day != ".DS_Store":
            date = f"2024-{month_num[month]}-{day}"
            file_path = f"/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/{
                month}/{day}"

            try:
                # Load NDVI data
                ndvi_data = rioxarray.open_rasterio(
                    f"{file_path}/NDVI_mosaic.tif").values
                avg = np.nanmean(ndvi_data)
                median = np.nanmedian(ndvi_data)
                std = np.nanstd(ndvi_data)
                var_coeff = std / avg if avg != 0 else np.nan

                # Load SCL data and upsample
                scl_data = rioxarray.open_rasterio(
                    f"{file_path}/SCL_mosaic.tif").values
                scl_data = np.kron(scl_data, np.ones((2, 2))
                                   )  # Upsample SCL data

                # Calculate statistics
                total_pixels = np.sum(~np.isnan(scl_data))
                veg_pixels = np.sum(scl_data == 4)
                masked_pixels = np.sum(
                    np.isin(scl_data, [3, 8, 9, 10, 11]) & ~np.isnan(scl_data))
                cloud_cover_pct = masked_pixels / total_pixels * 100
                veg_abundance_pct = veg_pixels / \
                    (total_pixels - masked_pixels) * 100

                # Create a new row and append it to the DataFrame
                new_row = pd.DataFrame([{
                    "date": date,
                    "total_pixels": total_pixels,
                    "veg_pixels": veg_pixels,
                    "masked_pixels": masked_pixels,
                    "cloud_cover_pct": cloud_cover_pct,
                    "veg_abundance_pct": veg_abundance_pct,
                    "avg_ndvi": avg,
                    "median_ndvi": median,
                    "std_ndvi": std,
                    "var_coeff_ndvi": var_coeff
                }])
                df = pd.concat([df, new_row], ignore_index=True)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

# Display the resulting DataFrame
print(df)

df["date"] = pd.to_datetime(df["date"])
df.sort_values("date", inplace=True)

# Save the DataFrame to a CSV file
df.to_csv("ndvi_data.csv", index=False)