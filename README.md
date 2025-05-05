# NDVI Processing and Visualization Project

Comprehensive tool for acquiring, processing, and visualizing Sentinel‑2 satellite imagery as Normalized Difference Vegetation Index (NDVI).

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Vegetation Health Metrics](#vegetation-health-metrics)
* [System Architecture](#system-architecture)
* [Pipeline Workflow](#pipeline-workflow)
* [About the Application](#about-the-application)
* [Use Cases](#use-cases)
* [Requirements & Installation](#requirements--installation)
* [Usage](#usage)
* [Contributing](#contributing)
* [Acknowledgments](#acknowledgments)
* [Contact](#contact)
* [Full Report](#full-report)

## Overview

This project automates the end‑to‑end processing of Sentinel‑2 imagery for a specified county (by FIPS code), producing Cloud Optimized GeoTIFFs (COGs) of:

* True‑color composites (RGB)
* NDVI
* Mosaic layers covering the study area

An interactive web app enables users to explore vegetation health patterns over time via pan/zoom map controls, temporal selectors, and basic analytics dashboards.

## Features

* **Automated Data Retrieval**: Query STAC catalog for Sentinel‑2 scenes intersecting a county boundary, filtering by cloud cover.
* **Geospatial Processing**: Clip, reproject, and mosaic multi‑scene imagery to a consistent CRS (EPSG:32611) for processing and EPSG:3857 for web visualization.
* **Cloud Masking**: Exclude clouds, shadows, and snow using Sentinel‑2 Scene Classification Layer (SCL).
* **NDVI Computation**: Compute (NIR – Red) / (NIR + Red) for each pixel, generating standardized NDVI layers.
* **COG Optimization**: Convert outputs to Cloud Optimized GeoTIFFs with internal tiling, compression, and overviews for efficient web delivery.
* **Statistical Summaries**: Calculate median, variance, vegetation abundance, and cloud cover percentages.
* **Tile Server API**: FastAPI + TiTiler backend to serve map tiles on demand.
* **Interactive Frontend**: Shiny for Python app with:

  * Date picker for available acquisition days
  * Layer toggles (RGB / NDVI)
  * Histograms and time series plots
  * Vegetation health indicators (Low, Moderate, High, Very High)

## Vegetation Health Metrics

| Metric                       | Definition                                                                         |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| **NDVI**                     | (NIR – Red) / (NIR + Red); range –1 to 1; vegetation typically 0.2–1.              |
| **Vegetation Abundance (%)** | Percentage of pixels with NDVI > 0.2, indicating healthy vegetation cover.         |
| **Variability Coefficient**  | Statistical variance of NDVI values, measuring heterogeneity of vegetation health. |
| **Cloud Cover (%)**          | Proportion of study area obscured by clouds or shadows during acquisition.         |

## System Architecture

```text
+----------------------+      +-----------------+      +-------------------------+
| Data Processing      | ---> | FastAPI +       | ---> | Shiny for Python Web    |
| (main.py)            |      | TiTiler Backend |      | Application (app.py)    |
+----------------------+      +-----------------+      +-------------------------+
```

1. **Data Processing Pipeline** (`main.py`) - use to aquire, process and store satellite imagery.
2. **Tile Server API** (`titiler_server.py`) - nessessary to serve processed satellite imagery to front-end application.
3. **Interactive Web UI** (`app.py`) - dynamically visualize processed imagery across a range of dates.

## Pipeline Workflow

1. **Scene Selection**: Query STAC for Sentinel‑2 scenes covering the county for each date.
2. **Band Extraction**: Retrieve Red, Green, Blue, NIR, and SCL bands.
3. **Clipping & Reprojection**: Clip to county boundary; reproject to EPSG:32611.
4. **Cloud Masking**: Mask out cloud, shadow, snow classes from SCL.
5. **NDVI Calculation**: Compute and save NDVI layer.
6. **RGB Composite**: Build true‑color composite with scaling and color correction.
7. **Mosaic Creation**: Merge multi‑scene tiles into seamless county‑wide mosaics.
8. **COG Optimization**: Generate COGs with tiling, compression, and overviews (20, 40, 80, 160, 320 m).
9. **Statistical Analysis**: Compute NDVI histograms, median, variance, abundance, and cloud metrics.

## About the Application

The Vegetation Health Monitoring Tool is a web-based application built with Shiny for Python that transforms complex Sentinel-2 satellite imagery into clear, actionable vegetation health insights. Developed as a capstone project for the University of Montana’s Master of Science in Business Analytics program, the application features two primary interfaces:

**Satellite Explorer**: Interactive map view with true-color and NDVI layers, pan/zoom controls, date selectors, and on-map health indicators.

**Analytics Dashboard**: Statistical charts, histograms, and time-series plots that illuminate vegetation trends, variability, and cloud cover quality over the growing season.

While this demo uses Missoula County as an example, the modular design allows you to adapt the pipeline and interface to any region or specific parcel of interest.

## Use Cases

### Agricultural Monitoring

For farmers and agricultural consultants, this tool offers early warning of crop stress by highlighting changes in NDVI across scales—from individual fields to entire farms. Example: Detecting reduced NDVI in a wheat field’s northeastern section to target irrigation before visible damage occurs.

### Forest Management

Forestry professionals can monitor forest stands or large forested regions to identify early signs of disease, pest infestations, or drought stress and to track recovery after disturbances like wildfires or logging. Example: Quantifying post-wildfire regeneration rates across multiple districts using time-series NDVI analysis.

### Urban Green Space Management

Urban planners and park managers can assess green infrastructure health across parks, neighborhoods, or cities, using vegetation abundance metrics to prioritize planting and maintenance efforts. Example: Evaluating NDVI improvements before and after a park renovation to support funding decisions.

### Conservation Area Monitoring

Conservation organizations can track the health of protected habitats—such as wetlands, watersheds, or large conservation lands—documenting seasonal patterns and long-term trends for grant reporting and ecological assessments. Example: Demonstrating wetland restoration success through rising NDVI values and vegetation abundance percentages.

## Requirements & Installation

1. **Clone the repo**:

   ```bash
   git clone https://github.com/andrew-engellant/satellite-to-NDVI.git
   cd satellite-to-NDVI
   ```

2. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure data paths** in `main.py` and `titiler_server.py` to point to your data directories.

## Usage

1. **Process imagery**:

   ```bash
   python main.py --fips <COUNTY_FIPS> --start 2024-04-01 --end 2024-10-31
   ```
   **Note:** *The FIPS code and date range can be adapted to match the desired geography and historic timeline*
*
2. **Start tile server**:

   ```bash
   python titiler_server.py
   ```
3. **Launch web app**:

   ```bash
   shiny run app.py --port 8050
   ```
4. **Browse**: Open `http://localhost:8050` in your browser.

## Contributing

Contributions are welcome! Please:

1. Fork the repo and create a feature branch.
2. Submit a pull request with tests and documentation.
3. Ensure code follows PEP 8 and includes docstrings.

## Acknowledgments

* Sentinel‑2 MSI Level‑2A data via ESA and Element84 Earth Search STAC API
* U.S. Census Bureau TIGER/Line county boundaries
* FastAPI, TiTiler, Shiny for Python, Rasterio, Rioxarray, Xarray

## Contact

Questions or feedback? Open an issue or reach out at [https://github.com/andrew-engellant](https://github.com/andrew-engellant).

## Full Report

For a detailed technical report, see the [capstone thesis PDF](https://github.com/andrew-engellant/satellite-to-NDVI/blob/main/capstone_written_product_final_ENGELLANT.pdf).
