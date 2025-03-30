import os
import requests
import numpy as np
import pickle

from shiny.express import input, render, ui
from shiny import reactive
from ipyleaflet import Map, TileLayer, basemaps, LayersControl
from shinywidgets import render_widget
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import savgol_filter
import pandas as pd
from shinyswatch import theme


# Base directory for your data (same as in TiTiler server)
BASE_DIR = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024'

# Load the NDVI data
ndvi_summary_df = pd.read_csv(
    '/Users/drewengellant/Documents/MSBA/Spring25/capstone/satellite-to-NDVI/ndvi_data.csv')
ndvi_summary_df['date'] = pd.to_datetime(
    ndvi_summary_df['date'])    # Convert date column to datetime

img_src = 'https://dailynewsnetwork.com/wp-content/uploads/2024/11/Morton-Primary-Stacked-Full-Color.png'

ui.page_opts(
    fillable=True,
    theme=theme.darkly
)

# Create a custom header div for the logo and title
ui.tags.div(
    ui.tags.div(
        ui.tags.img(src=img_src, height="60px", style="margin: 10px 0;"),
        ui.tags.h2("Vegetation Health Monitoring Tool",
                   style="margin: 0 0 0 20px; color:rgb(11, 28, 45); font-size: 36px; font-weight: 600; display: inline-block;"),
        style="display: flex; align-items: center; padding: 5px 15px;"
    ),
    style="background-color: white; border-bottom: 1px solid #e5e5e5;"
)

# Style the nav bar
ui.tags.style("""
    .nav-tabs .nav-link {
        font-size: 20px;
        font-weight: 500;
    }
""")

# Create the navigation panels
with ui.navset_card_tab():
    with ui.nav_panel("Satellite Explorer"):
        # Create layout with a sticky sidebar
        with ui.layout_sidebar(sidebar_panel_fixed=False):
            # Sidebar with controls
            with ui.sidebar(width=200):
                ui.h4("Date Selection")

                ui.input_select(
                    "sat_month_select",
                    "Month:",
                    choices=[
                        "April", "May", "June", "July",
                        "August", "September", "October"
                    ],
                    selected="June"
                )

                # This will be populated based on the selected month
                ui.input_select(
                    "sat_day_select",
                    "Day:",
                    choices=[]
                )

            # Main panel content
            with ui.layout_columns(col_widths=(4, 4, 4)):
                with ui.card():
                    ui.div(id="sat_ndvi_category_container")
                with ui.card():
                    ui.div(id="sat_variability_category_container")
                with ui.card():
                    ui.div(id="sat_cloud_cover_container")

            ui.h1("Satellite Imagery Viewer",
                  style="font-size: 28px; margin-bottom: 10px;")
            with ui.card(height="800px"):
                @render_widget
                def map_widget():
                    # Get selected month and day
                    month = input.sat_month_select()
                    day = input.sat_day_select()

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
                            zoom=10, scroll_wheel_zoom=True)

                    # Add OpenStreetMap base layer
                    m.add_layer(basemaps.Esri.WorldGrayCanvas)

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

    with ui.nav_panel("Analytics"):
        # Create layout with a sticky sidebar
        with ui.layout_sidebar(sidebar_panel_fixed=False):
            # Sidebar with controls
            with ui.sidebar(width=200):
                ui.h4("Date Selection")

                ui.input_select(
                    "analysis_month_select",
                    "Month:",
                    choices=[
                        "April", "May", "June", "July",
                        "August", "September", "October"
                    ],
                    selected="June"
                )

                # This will be populated based on the selected month
                ui.input_select(
                    "analysis_day_select",
                    "Day:",
                    choices=[]
                )
            with ui.layout_columns(col_widths=(5, 7)):
                with ui.card(height="300px"):
                    @render.plot(alt="NDVI histogram")
                    def plot_hist():
                        month = input.analysis_month_select()
                        day = input.analysis_day_select()

                        # Check for valid inputs
                        if not month or not day or day == "None":
                            # Return an empty plot if inputs are invalid
                            fig, ax = plt.subplots()
                            ax.text(0.5, 0.5, "Select a valid date to display data",
                                    ha='center', va='center', transform=ax.transAxes)
                            ax.set_axis_off()
                            return fig
                        # Construct the path to the pickle file
                        pickle_path = f"{BASE_DIR}/{month}/{day}_hist.pkl"

                        # Load the histogram data from the pickle file
                        with open(pickle_path, 'rb') as f:
                            histogram_data = pickle.load(f)

                        # Create the histogram using the pre-computed data
                        fig, ax = plt.subplots()

                        # Plot histogram using the saved bin counts and edges
                        ax.bar(histogram_data['bins'][:-1],
                               histogram_data['counts'],
                               width=np.diff(histogram_data['bins']),
                               alpha=0.5,
                               color='#6053E4',
                               label='NDVI Values')

                        ax.set_title(
                            'Distribution of Vegetation Index (NDVI) Values')
                        ax.set_xlabel('NDVI Value')
                        ax.set_ylabel('Abundance')
                        ax.set_ylim(0, 8000000)  # Set y-axis limits

                        # Remove the box around the plot
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        ax.spines['left'].set_visible(False)
                        ax.spines['bottom'].set_visible(False)

                        # Plot the median line using the saved median value
                        median_ndvi = histogram_data['median']
                        ax.axvline(x=median_ndvi, color='red', linestyle='-',
                                   label=f'Median: {median_ndvi:.2f}')
                        # Increase handle length to make space for the Median: legend
                        ax.legend(loc='upper left')

                        return fig

                        # Right column: Timeseries plot
                with ui.layout_columns(col_widths=(12)):
                    with ui.card(height="300px"):
                        @render.plot(alt="NDVI timeseries")
                        def plot_veg_health_timeseries(ndvi_data=ndvi_summary_df):
                            month = input.analysis_month_select()
                            day = input.analysis_day_select()

                            # Check for valid inputs
                            if not month or not day or day == "None":
                                # Return an empty plot if inputs are invalid
                                fig, ax = plt.subplots(figsize=(12, 6))
                                ax.text(0.5, 0.5, "Select a valid date to display data",
                                        ha='center', va='center', transform=ax.transAxes)
                                ax.set_axis_off()
                                return fig

                            # Convert date column to datetime
                            ndvi_data['date'] = pd.to_datetime(
                                ndvi_data['date'])

                            # Create a date string for the selected date
                            selected_date_str = f"2024-{month}-{day}"
                            selected_date = pd.to_datetime(selected_date_str)
                            # Apply the filtering conditions
                            filtered_df = ndvi_data[(ndvi_data['cloud_cover_pct'] <= 50) & (
                                ndvi_data['total_pixels'] >= 50000000)]

                            # Sort by date for proper time series plotting
                            filtered_df = filtered_df.sort_values('date')

                            # Apply a Savitzky-Golay filter for smoothing
                            smoothed_ndvi = savgol_filter(
                                filtered_df['median_ndvi'], window_length=7, polyorder=3, mode='nearest')

                            # Create figure with appropriate size
                            fig, ax = plt.subplots(figsize=(12, 6))

                            # Plot the original data
                            ax.scatter(filtered_df['date'], filtered_df['median_ndvi'],
                                       marker='o', color='#6053E4', label='Raw NDVI')

                            # Plot the smoothed trend
                            ax.plot(filtered_df['date'], smoothed_ndvi, linestyle='-',
                                    linewidth=2, label='Smoothed Trend', color='red')

                            # Check if the selected date is in the filtered dataframe
                            selected_data = filtered_df[filtered_df['date']
                                                        == selected_date]

                            if not selected_data.empty:
                                # Highlight the selected date with a different color
                                ax.scatter(selected_data['date'], selected_data['median_ndvi'],
                                           marker='o', color='#1F1740', s=100, zorder=5)

                            else:
                                # Check if the date exists in the original data but was filtered out
                                original_selected = ndvi_data[ndvi_data['date']
                                                              == selected_date]

                                if not original_selected.empty:
                                    # Show message that the date was excluded
                                    ax.text(0.58, 0.1,
                                            f"Note: {month} {
                                                day} was excluded due\nto insufficient coverage or visibility.",
                                            transform=ax.transAxes, ha='center',
                                            bbox=dict(facecolor='lightyellow', alpha=0.5, boxstyle='round'), fontsize=16)

                            # Formatting
                            ax.set_title('Vegatation Health Over Time')
                            ax.set_ylabel('Median NDVI')
                            ax.legend(loc='upper left')
                            ax.grid(False)
                            ax.xaxis.set_major_formatter(
                                mdates.DateFormatter('%B'))

                            # Remove the box around the plot
                            ax.spines['top'].set_visible(False)
                            ax.spines['right'].set_visible(False)
                            ax.spines['left'].set_visible(False)
                            ax.spines['bottom'].set_visible(False)

                            return fig

                    with ui.card(height="300px"):
                        @render.plot(alt="Abundance timeseries")
                        def plot_veg_pct_timeseries(ndvi_data=ndvi_summary_df):
                            month = input.analysis_month_select()
                            day = input.analysis_day_select()

                            # Check for valid inputs
                            if not month or not day or day == "None":
                                # Return an empty plot if inputs are invalid
                                fig, ax = plt.subplots(figsize=(12, 6))
                                ax.text(0.5, 0.5, "Select a valid date to display data",
                                        ha='center', va='center', transform=ax.transAxes)
                                ax.set_axis_off()
                                return fig

                            # Convert date column to datetime
                            ndvi_data['date'] = pd.to_datetime(
                                ndvi_data['date'])

                            # Create a date string for the selected date
                            selected_date_str = f"2024-{month}-{day}"
                            selected_date = pd.to_datetime(selected_date_str)
                            # Apply the filtering conditions
                            filtered_df = ndvi_data[(ndvi_data['cloud_cover_pct'] <= 50) & (
                                ndvi_data['total_pixels'] >= 50000000)]

                            # Sort by date for proper time series plotting
                            filtered_df = filtered_df.sort_values('date')

                            # Apply a Savitzky-Golay filter for smoothing
                            smoothed_ndvi = savgol_filter(
                                filtered_df['veg_abundance_pct'], window_length=7, polyorder=3, mode='nearest')

                            # Create figure with appropriate size
                            fig, ax = plt.subplots(figsize=(12, 6))

                            # Plot the original data
                            ax.scatter(filtered_df['date'], filtered_df['veg_abundance_pct'],
                                       marker='o', color='#6053E4', label='Raw NDVI')

                            # Plot the smoothed trend
                            ax.plot(filtered_df['date'], smoothed_ndvi, linestyle='-',
                                    linewidth=2, label='Smoothed Trend', color='red')

                            # Check if the selected date is in the filtered dataframe
                            selected_data = filtered_df[filtered_df['date']
                                                        == selected_date]

                            if not selected_data.empty:
                                # Highlight the selected date with a different color
                                ax.scatter(selected_data['date'], selected_data['veg_abundance_pct'],
                                           marker='o', color='#1F1740', s=100, zorder=5)

                            # else:
                            #     # Check if the date exists in the original data but was filtered out
                            #     original_selected = ndvi_data[ndvi_data['date'] == selected_date]

                            #     if not original_selected.empty:
                            #         # Show message that the date was excluded
                            #         ax.text(0.58, 0.1,
                            #             f"Note: {month} {day} was excluded due\nto insufficient coverage or visibility.",
                            #             transform=ax.transAxes, ha='center',
                            #             bbox=dict(facecolor='lightyellow', alpha=0.5, boxstyle='round'), fontsize=16)

                            # Formatting
                            ax.set_title('Vegatation Abundance Over Time')
                            ax.set_ylabel(
                                'Percent Coverage of Missoula County')
                            ax.legend(loc='upper left')
                            ax.grid(False)
                            ax.xaxis.set_major_formatter(
                                mdates.DateFormatter('%B'))

                            # Remove the box around the plot
                            ax.spines['top'].set_visible(False)
                            ax.spines['right'].set_visible(False)
                            ax.spines['left'].set_visible(False)
                            ax.spines['bottom'].set_visible(False)

                            return fig

    with ui.nav_panel("About"):
        with ui.layout_sidebar(sidebar_width=300):
            # Sidebar with controls for demo purposes
            with ui.sidebar():
                ui.h4("Demonstration Controls")

                ui.input_select(
                    "about_use_case",
                    "Example Use Case:",
                    choices={
                        "agriculture": "Agricultural Monitoring",
                        "forestry": "Forest Management",
                        "urban": "Urban Green Space",
                        "conservation": "Conservation Area"
                    },
                    selected="agriculture"
                )

                ui.input_select(
                    "about_scale_slider",
                    "Scale of Analysis:",
                    choices={
                        "1": "Field",
                        "2": "Farm/Stand",
                        "3": "Watershed/Regional",
                        "4": "County"
                    },
                    selected="2"
                )

                ui.hr()

                ui.h4("Learn More")
                ui.a("NDVI Explained",
                     href="https://earthobservatory.nasa.gov/features/MeasuringVegetation", target="_blank")
                ui.br()
                ui.a("Sentinel-2 Satellite",
                     href="https://sentinel.esa.int/web/sentinel/missions/sentinel-2", target="_blank")
                ui.br()
                ui.a("Contact Us", href="mailto:andrew.engellant@umontana.edu")

            # Main content
            with ui.card(fill=False):
                ui.h1("About the Vegetation Health Monitoring Tool")

                ui.h2("Understanding This Tool")

                ui.p("""
                    Welcome to the Vegetation Health Monitoring Tool, a powerful web application designed to transform complex satellite 
                    imagery into accessible vegetation health insights. This tool was developed as part of a capstone project at the 
                    University of Montana's Master of Science in Business Analytics program to demonstrate how satellite data can be 
                    made accessible and actionable for land management professionals, agricultural consultants, and environmental researchers.
                """)

                ui.p("""
                    While this demonstration focuses on Missoula County, the technology behind it is designed to be adaptable 
                    for monitoring specific parcels of land, farms, forests, or watersheds according to your needs.
                """)

            # Interactive example section
            with ui.card(fill=False):
                @render.ui
                def example_content():
                    use_case = input.about_use_case()
                    scale = int(input.about_scale_slider())

                    use_case_content = {
                        "agriculture": {
                            "title": "Agricultural Monitoring",
                            "description": f"""
                                For agricultural consultants and farmers, this tool provides critical insights into crop health and
                                development across {'individual fields' if scale == 1 else 'entire farms' if scale == 2 else 'regional growing areas' if scale == 3 else 'county-wide agricultural lands'}.
                                The vegetation index (NDVI) highlights areas of crop stress before they become visible to the naked eye,
                                enabling timely intervention.
                            """,
                            "example": f"""
                                Example: A consultant monitors a {'wheat field' if scale <= 2 else 'farming region'} and notices reduced NDVI
                                values in the northeastern section. This early detection of irrigation issues allows for targeted
                                intervention, potentially saving the crop before visible symptoms appear.
                            """
                        },
                        "forestry": {
                            "title": "Forest Management",
                            "description": f"""
                                Forestry professionals can use this tool to monitor {'specific forest stands' if scale <= 2 else 'large forested regions' if scale == 3 else 'county-wide forest resources'}.
                                The temporal analysis capabilities help detect early signs of disease, pest infestations, or drought stress,
                                and track recovery after wildfires or logging operations.
                            """,
                            "example": f"""
                                Example: A forest manager monitors a {'recently thinned stand' if scale <= 2 else 'watershed after a controlled burn' if scale == 3 else 'post-wildfire recovery across multiple districts'}.
                                By tracking NDVI values over time, they can quantify vegetation recovery rates and adjust management
                                strategies accordingly.
                            """
                        },
                        "urban": {
                            "title": "Urban Green Space Management",
                            "description": f"""
                                Urban planners and park managers can use this tool to assess green infrastructure across
                                {'individual parks' if scale == 1 else 'neighborhoods' if scale == 2 else 'entire cities' if scale == 3 else 'multiple municipalities'}.
                                The vegetation abundance metrics help quantify green coverage and identify areas that may benefit from
                                additional planting or maintenance.
                            """,
                            "example": f"""
                                Example: A city planner evaluates the effectiveness of a {'park renovation project' if scale <= 2 else 'city-wide green infrastructure initiative' if scale == 3 else 'regional urban forest conservation plan'}.
                                By comparing NDVI values before and after implementation, they can document improvements in vegetation health
                                and justify continued funding.
                            """
                        },
                        "conservation": {
                            "title": "Conservation Area Monitoring",
                            "description": f"""
                                Conservation organizations can leverage this tool to track the health of protected natural areas ranging from
                                {'specific habitat restoration sites' if scale <= 2 else 'entire watersheds' if scale == 3 else 'county-wide conservation lands'}.
                                The time-series analysis helps document seasonal patterns and long-term trends in vegetation health.
                            """,
                            "example": f"""
                                Example: A watershed protection group monitors a {'wetland restoration project' if scale <= 2 else 'river corridor restoration' if scale == 3 else 'landscape-scale conservation initiative'}.
                                The increasing NDVI values and vegetation abundance percentages provide objective evidence of
                                ecological recovery for grant reporting and future funding requests.
                            """
                        }
                    }

                    content = use_case_content[use_case]

                    return ui.div(
                        ui.h3(content["title"] + f" at {
                              ['Field', 'Farm/Stand', 'Watershed/Regional', 'County'][scale-1]} Scale"),
                        ui.p(content["description"]),
                        ui.p(content["example"], style="font-style: italic;"),
                        ui.p(
                            "Try changing the use case and scale in the sidebar to see how this tool can be adapted for different applications.")
                    )
            with ui.card(fill=False):
                ui.h2("How to Use This Tool")

                ui.p("""
                    The Vegetation Health Monitoring Tool features two main interfaces: the Satellite Explorer and the Analytics dashboard. 
                    Here's how to make the most of each:
                """)

                with ui.layout_columns(col_widths=[6, 6]):
                    with ui.card(fill=False):
                        ui.h3("Satellite Explorer")
                        ui.p("""
                            The Satellite Explorer tab allows you to visually examine satellite imagery of the landscape and its corresponding 
                            vegetation health representation.
                        """)

                        ui.h4("Key Features:")
                        with ui.tags.ul():
                            ui.tags.li(
                                "Select specific dates using the month and day dropdown menus")
                            ui.tags.li(
                                "Pan and zoom the map to explore different areas")
                            ui.tags.li(
                                "Toggle between layers to compare true-color imagery and vegetation health visualization")
                            ui.tags.li(
                                "View key metrics in the status boxes above the map")

                        ui.h4("Understanding the Health Indicators:")
                        ui.p("""
                            The status boxes provide at-a-glance information about vegetation conditions on the selected date:
                        """)
                        with ui.tags.ul():
                            ui.tags.li(
                                "Vegetation Health Status: Categorizes the overall vegetation vigor")
                            ui.tags.li(
                                "Vegetation Health Variability: Indicates how uniform the vegetation health is across the landscape")
                            ui.tags.li(
                                "Cloud Coverage: Shows the percentage of the area obscured by clouds, which affects data quality")

                    with ui.card(fill=False):
                        ui.h3("Analytics")
                        ui.p("""
                            The Analytics tab provides more detailed information about vegetation health patterns and trends.
                        """)

                        ui.h4("Key Features:")
                        with ui.tags.ul():
                            ui.tags.li(
                                "Histogram showing the distribution of vegetation health values across the landscape")
                            ui.tags.li(
                                "Time-series charts tracking vegetation health and abundance throughout the growing season")
                            ui.tags.li(
                                "Selected date highlighted on the time-series for context")
                            ui.tags.li(
                                "Smoothed trend lines revealing seasonal patterns")

                        ui.h4("Reading the Charts:")
                        ui.p("""
                            The time-series charts filter out low-quality observations (high cloud cover or incomplete coverage)
                            to ensure reliable trend analysis. The smoothed red line helps identify the seasonal pattern beyond 
                            day-to-day variations.
                        """)
                        ui.p("""
                            A selected date that doesn't appear on the time-series indicates it was excluded due to quality issues,
                            which will be noted on the chart.
                        """)

            with ui.card(fill=False):
                ui.h2("Beyond the Demo: Customization Potential")

                ui.p("""
                    This website demonstrates the overall capabilities of the Vegetation Health Monitoring Tool using Missoula County 
                    as an example. However, the underlying technology was intentionally designed for flexibility and customization.
                """)

                ui.p("""
                    The data pipeline can be easily adjusted to:
                """)

                with ui.tags.ul():
                    ui.tags.li(
                        ui.tags.b("Focus on specific properties:"),
                        """ By changing a single variable, the system can be reconfigured to monitor 
                        a private farm, forest stand, or conservation area instead of an entire county
                        """
                    )

                    ui.tags.li(
                        ui.tags.b("Adjust the time range:"),
                        " The date range can span a decade of historical data or focus on real-time monitoring, depending on your needs"
                    )

                    ui.tags.li(
                        ui.tags.b("Add specialized metrics:"),
                        """ While this demo uses NDVI (Normalized Difference Vegetation Index) 
                        as a standard vegetation health measure, the modular pipeline design allows for easy addition of specialized 
                        indices for specific vegetation types, moisture monitoring, or crop classification
                        """
                    )

                ui.p("""
                    For ethical reasons, this demonstration was restricted to publicly available data covering an entire county rather than 
                    focusing on private property without consent. However, agricultural consultants, forestry managers, or conservation organizations 
                    can implement this technology for detailed analysis of specific lands with proper authorization.
                """)

                ui.h2("Technical Foundation")

                ui.p("""
                    While you don't need to understand the technical details to use this tool effectively, it may be helpful to know that it's built on:
                """)

                with ui.tags.ul():
                    ui.tags.li(
                        "European Space Agency's Sentinel-2 satellite imagery with 10-meter resolution")
                    ui.tags.li(
                        "Automated cloud detection and masking to ensure data quality")
                    ui.tags.li(
                        "Statistical analysis that filters out poor quality observations")
                    ui.tags.li(
                        "Temporal smoothing to reveal underlying patterns despite day-to-day variability")

                ui.p("""
                    The satellite revisits each area approximately every 3-5 days, providing frequent updates during the growing season. 
                    However, cloud coverage or technical issues may result in gaps in the available dates.
                """)

                ui.h2("Future Applications")

                ui.p("""
                    This demonstration represents just the beginning of what's possible with satellite-based vegetation monitoring. 
                    Future enhancements could include:
                """)

                with ui.tags.ul():
                    ui.tags.li(
                        "Integration of weather data to correlate vegetation patterns with precipitation and temperature")
                    ui.tags.li(
                        "Machine learning models for crop classification or invasive species detection")
                    ui.tags.li(
                        "Automated alerting when vegetation health falls below defined thresholds")
                    ui.tags.li(
                        "Predictive analytics to forecast seasonal patterns based on historical data")
                    ui.tags.li(
                        "Higher resolution imagery for monitoring smaller parcels or specialized crops")

                ui.p("""
                    By making powerful remote sensing technology accessible to non-technical users, tools like this help bridge the gap 
                    between advanced earth observation capabilities and practical land management decision-making.
                """)

                ui.hr()

                ui.p("""
                    This tool was developed by Andrew Engellant as a capstone project for the Master of Science in Business Analytics 
                    program at the University of Montana, completed in March 2025.
                """, style="font-style: italic;")


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

# For Satellite Viewer tab


@reactive.effect
@reactive.event(lambda: input.sat_month_select())
def update_sat_day_dropdown():
    month = input.sat_month_select()
    days = get_available_days(month)

    # Sort days numerically
    days.sort(key=lambda x: int(x))

    # Format days for display (remove leading zeros)
    day_choices = {day: str(int(day)) for day in days}

    # Set default day to 21 if the month is July
    selected_day = "21" if month == "June" and "21" in days else (
        days[0] if days else None)

    ui.update_select(
        "sat_day_select",
        choices=day_choices,
        selected=selected_day  # Set default day to 21 if applicable
    )

# For Analysis tab


@reactive.effect
@reactive.event(lambda: input.analysis_month_select())
def update_analysis_day_dropdown():
    month = input.analysis_month_select()
    days = get_available_days(month)

    # Sort days numerically
    days.sort(key=lambda x: int(x))

    # Format days for display (remove leading zeros)
    day_choices = {day: str(int(day)) for day in days}

    # Set default day to 21 if the month is June
    selected_day = "21" if month == "June" and "21" in days else (
        days[0] if days else None)

    ui.update_select(
        "analysis_day_select",  # Updated
        choices=day_choices,
        selected=selected_day
    )


@reactive.effect
@reactive.event(lambda: [input.sat_month_select(), input.sat_day_select()])
def update_value_boxes():
    month = input.sat_month_select()
    day = input.sat_day_select()

    # Skip if no month or day is selected, or if day is None
    if not month or not day or day == "None":
        print(f"Skipping update_value_boxes: month={month}, day={day}")
        return

    try:
        # Format the date to match the format in your CSV (YYYY-MM-DD)
        # Pad the day with a leading zero if needed
        day_padded = day.zfill(2) if len(day) == 1 else day

        # Create date string in format "2024-April-02"
        # Then convert it to datetime for comparison
        date_str = f"2024-{month}-{day_padded}"
        selected_date = pd.to_datetime(date_str)

        # Filter the dataframe for the matching date
        selected_data = ndvi_summary_df[ndvi_summary_df['date']
                                        == selected_date]

        if selected_data.empty:
            print(f"No data found for date: {selected_date}")
            return

        # Get median NDVI value
        median_ndvi = selected_data['median_ndvi'].iloc[0]

        # Get the variability coefficient
        if 'var_coeff_ndvi' in selected_data.columns:
            var_coeff = selected_data['var_coeff_ndvi'].iloc[0]
        elif 'std_ndvi' in selected_data.columns and median_ndvi != 0:
            # Calculate coefficient of variation if not directly available
            std_ndvi = selected_data['std_ndvi'].iloc[0]
            var_coeff = std_ndvi / median_ndvi
        else:
            var_coeff = 0.17  # Default value

        # Get cloud cover percentage
        cloud_cover_pct = round(selected_data['cloud_cover_pct'].iloc[0], 1)

        # Update both value boxes
        update_sat_ndvi_category(median_ndvi)
        update_sat_variability_category(var_coeff)
        update_sat_cloud_category(cloud_cover_pct)

    except Exception as e:
        print(f"Error updating value boxes: {e}")


def update_sat_ndvi_category(median_ndvi):
    """Update the NDVI category value box based on the median NDVI value"""
    if median_ndvi < 0.65:
        category = "LOW"
        color = "danger"
        description = "Minimal vegetation density"
    elif median_ndvi < 0.7:
        category = "MODERATE"
        color = "warning"
        description = "Moderate vegetation density"
    elif median_ndvi < 0.75:
        category = "HIGH"
        color = "success"
        description = "High vegetation density"
    else:
        category = "VERY HIGH"
        color = "primary"
        description = "Very high vegetation density"

    # Remove current content and create a new value box
    ui.remove_ui("#sat_ndvi_category_container > *")

    # Fix the lambda function issue by creating the UI element first
    value_box = ui.value_box(
        title="Vegetation Health Status:",
        value=category,
        theme=color,
        description=description,
        height="120px"
    )

    # Then pass it to insert_ui
    ui.insert_ui(
        selector="#sat_ndvi_category_container",
        ui=value_box
    )


def update_sat_variability_category(var_coeff):
    """Update the variability category value box based on var_coeff_ndvi"""
    if var_coeff < 0.165:
        category = "LOW"
        color = "success"
        description = "Low variation across the landscape"
    elif var_coeff < 0.185:
        category = "MODERATE"
        color = "warning"
        description = "Moderate variation across the landscape"
    else:
        category = "HIGH"
        color = "danger"
        description = "High variation across the landscape"

    # Remove current content and create a new value box
    ui.remove_ui("#sat_variability_category_container > *")

    # Fix the lambda function issue by creating the UI element first
    value_box = ui.value_box(
        title="Vegetation Health Variability:",
        value=category,
        theme=color,
        description=description,
        height="120px"
    )

    # Then pass it to insert_ui
    ui.insert_ui(
        selector="#sat_variability_category_container",
        ui=value_box
    )


def update_sat_cloud_category(cloud_cover_pct):
    """Update the Cloud Cover % value box based on the cloud cover percentage"""
    # Remove current content and create a new value box
    value = f"{cloud_cover_pct}%"

    ui.remove_ui("#sat_cloud_cover_container > *")

    # Fix the lambda function issue by creating the UI element first
    value_box = ui.value_box(
        title="Cloud Coverage:",
        value=value,
        theme="primary",
        description="Cloud Cover Percentage",
        height="120px"
    )

    # Then pass it to insert_ui
    ui.insert_ui(
        selector="#sat_cloud_cover_container",
        ui=value_box
    )

# Initialize the value boxes on app startup


@reactive.effect
def initialize_value_boxes():
    # Create initial value boxes with default values
    update_sat_ndvi_category(0.68)
    update_sat_variability_category(0.17)
    update_sat_cloud_category(0)