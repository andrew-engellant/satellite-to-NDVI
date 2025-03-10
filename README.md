# NDVI Processing and Visualization Project

## Overview

This project is designed to process Sentinel-2 satellite imagery to compute and visualize the Normalized Difference Vegetation Index (NDVI) for specified dates within a given geographic area defined by a county's FIPS code. The workflow includes setting up the environment, searching for relevant satellite scenes, clipping and masking bands, computing NDVI, saving the results as Cloud Optimized GeoTIFFs, and creating mosaics for visualization.

The project consists of three main components:
1. **Data Processing Script (`main.py`)**: Handles the downloading, processing, and saving of NDVI data.
2. **Web Server (`titiler_server.py`)**: Sets up a FastAPI server to serve the processed raster data as tiles.
3. **Web Application (`app.py`)**: A Shiny web application for visualizing the NDVI and RGB imagery.

## Features

- **Data Processing**: Automates the retrieval and processing of Sentinel-2 imagery, including cloud masking and NDVI computation.
- **Web Server**: Provides an API to access processed raster data as Cloud Optimized GeoTIFFs.
- **Interactive Visualization**: Allows users to select dates and visualize NDVI and RGB imagery on a map.

## Requirements

To run this project, you will need the following Python packages:

- `geopandas`
- `numpy`
- `rasterio`
- `rioxarray`
- `xarray`
- `pystac-client`
- `fastapi`
- `uvicorn`
- `shiny`
- `ipyleaflet`
- `shinywidgets`

You can install the required packages using pip:


```bash
pip install geopandas numpy rasterio rioxarray xarray pystac-client fastapi uvicorn shiny ipyleaflet shinywidgets
```


## Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/andrew-engellant/satellite-to-NDVI.git
   cd satellite-to-NDVI
   ```

2. **Set Up the Environment**:
   Ensure you have the necessary data files and directories set up as specified in the scripts. The project expects a directory structure similar to:
   ```
   /Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024
   ```

3. **Run the Data Processing Script**:
   Execute the `main.py` script to process the Sentinel-2 imagery:
   ```bash
   python main.py
   ```

4. **Start the Web Server**:
   Run the FastAPI server to serve the processed data:
   ```bash
   python titiler_server.py
   ```

5. **Launch the Web Application**:
   Open a new terminal and run the Shiny app using a different port:
   ```bash
   shiny run app.py --port 8050
   ```

6. **Access the Application**:
   Open your web browser and navigate to `http://localhost:8050` to view the application.

## Usage

- **Select a Month and Day**: Use the sidebar to select a month and day for which you want to visualize the NDVI and RGB imagery.
- **View the Map**: The map will display the selected imagery, allowing you to toggle between RGB and NDVI layers.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## Acknowledgments

- This project utilizes Sentinel-2 satellite imagery and the STAC API for data retrieval.
- Thanks to the developers of the libraries used in this project for their contributions to the open-source community.

## Contact

For any questions or feedback, please reach out to https://github.com/andrew-engellant.