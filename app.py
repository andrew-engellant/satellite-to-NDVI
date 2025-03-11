"""
This script is a Shiny web application for visualizing raster data. 
It allows users to select a month and day to view corresponding RGB and NDVI imagery 
from a TiTiler server. The application features a sidebar for date selection, 
displays a map with layers for RGB and NDVI imagery, and includes server status 
indicators to show connectivity to the TiTiler server. The day dropdown is dynamically 
updated based on the selected month, fetching available days from the server or 
falling back to directory scanning if the server is not reachable.
"""

import os
import requests

from shiny.express import input, render, ui
from shiny import reactive  # Corrected import
from ipyleaflet import Map, TileLayer, basemaps, LayersControl
from shinywidgets import render_widget

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import savgol_filter
import pandas as pd
import numpy as np
import rasterio

# TODO: Adjust layout to include scrollable page
# TODO: Create pickle file for the NDVI histogram for each day

# Base directory for your data (same as in TiTiler server)
BASE_DIR = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024'

# Load the NDVI data
ndvi_summary_df = pd.read_csv('/Users/drewengellant/Documents/MSBA/Spring25/capstone/satellite-to-NDVI/ndvi_data.csv')
ndvi_summary_df['date'] = pd.to_datetime(ndvi_summary_df['date'])    # Convert date column to datetime

# Add title
ui.page_opts(title="Raster Viewer", fillable=True)

# Create layout
with ui.layout_sidebar():
    # Sidebar with controls
    with ui.sidebar(width=300):
        ui.h4("Date Selection")

        ui.input_select(
            "month_select",
            "Month:",
            choices=[
                "April", "May", "June", "July",
                "August", "September", "October"
            ],
            selected="April"
        )

        # This will be populated based on the selected month
        ui.input_select(
            "day_select",
            "Day:",
            choices=[]
        )

    # Main panel with map
    with ui.layout_columns():
        with ui.card(height="600px"):
            ui.card_header("Map View")

            @render_widget
            def map_widget():
                # Get selected month and day
                month = input.month_select()
                day = input.day_select()

                # Check if selections are valid
                if not month or not day:
                    # Return a simple map with just the base layer if no data selected
                    m = Map(center=(46.8721, -113.9940), zoom=12)
                    return m

                # Construct the tile URL for the RGB raster
                rgb_tile_url = (
                    f"http://localhost:8000/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?"
                    f"url=file://{BASE_DIR}/{month}/{day}/RGB_mosaic.tif"
                    f"&bidx=1&bidx=2&bidx=3"
                )

                # Construct the tile URL for the NDVI raster
                ndvi_tile_url = (
                    f"http://localhost:8000/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?"
                    f"url=file://{BASE_DIR}/{month}/{day}/NDVI_mosaic.tif"
                    f"&colormap_name=rdylgn"
                    f"&rescale=0.01,1"
                    f"&nodata=nan"
                    f"&return_mask=true"
                )

                # Create the map
                m = Map(center=(46.8721, -113.9940),
                        zoom=12, scroll_wheel_zoom=True)

                # Add OpenStreetMap base layer
                m.add_layer(basemaps.OpenStreetMap.Mapnik)

                # Add RGB tile layer - visible by default
                rgb_layer = TileLayer(
                    url=rgb_tile_url,
                    name="RGB Imagery",
                    attribution="RGB Imagery via TiTiler"
                )
                m.add_layer(rgb_layer)

                # Add NDVI tile layer - initially invisible
                ndvi_layer = TileLayer(
                    url=ndvi_tile_url,
                    name="NDVI Imagery",
                    attribution="NDVI Imagery via TiTiler",
                    opacity=1.0,
                    visible=True  # Set this to False to hide the layer initially
                )
                m.add_layer(ndvi_layer)

                # Add layer control
                m.add_control(LayersControl(position='topright'))

                return m
    
    
    with ui.layout_columns():           
        with ui.layout_columns():
            with ui.card():
                @render.plot(alt="NDVI histogram")  
                def plot_hist():  
                    month = input.month_select()
                    day = input.day_select()

                    # Construct the tile URL for the NDVI raster
                    raster_path = f"{BASE_DIR}/{month}/{day}/NDVI_mosaic.tif"
                    with rasterio.open(raster_path) as src:
                        ndvi_array = src.read(1)
                        
                        # Update histogram plotting
                        fig, ax = plt.subplots()
                        ax.hist(ndvi_array[~np.isnan(ndvi_array)], 25, alpha=0.5, label='NDVI Values', range=(0.2, 1))
                        ax.set_title('Histogram of NDVI Values')
                        ax.set_xlabel('NDVI Value')
                        ax.set_ylabel('Frequency')
                        
                        # Calculate and plot the median
                        median_ndvi = np.nanmedian(ndvi_array)
                        ax.axvline(x=median_ndvi, color='red', linestyle='-', label=f'Median: {median_ndvi:.2f}')
                        ax.legend()
                        
                        return fig
    
            with ui.card():
                @render.plot(alt="NDVI timeseries")  
                def plot_timeseries(ndvi_data=ndvi_summary_df):  
                    month = input.month_select()
                    day = input.day_select()
                    # TODO: Implement user input to highlight selected day on the plot

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

                    fig = plt.gcf()
                    return fig


# Function to get available days from the server


def get_available_days(month):
    try:
        response = requests.get("http://localhost:8000/available_days")
        if response.status_code == 200:
            data = response.json()
            if month in data:
                return data[month]
        return []
    except:
        # Fallback to direct directory scanning
        month_path = os.path.join(BASE_DIR, month)
        if os.path.isdir(month_path):
            return [
                d for d in os.listdir(month_path)
                if os.path.isdir(os.path.join(month_path, d))
            ]
        return []
    
    
@reactive.effect
@reactive.event(lambda: input.month_select())
def update_day_dropdown():
    month = input.month_select()
    days = get_available_days(month)

    # Sort days numerically
    days.sort(key=lambda x: int(x))

    # Format days for display (remove leading zeros)
    day_choices = {day: str(int(day)) for day in days}

    ui.update_select(
        "day_select",
        choices=day_choices,
        selected=days[0] if days else None
    )

