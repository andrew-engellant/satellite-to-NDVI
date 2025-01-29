import geopandas as gpd
import matplotlib.pyplot as plt
import os

os.chdir("/Volumes/Drew_ext_drive/NDVI_Proj") # Set directory to project folder

def load_county_geometry(fips_code):
    """
    Loads the geometry for a specified county based on its FIPS code from the Montana TIGER shapefile.
    
    Parameters:
    fips_code (str): The FIPS code of the county to load. MSO County = 063
    
    Returns:
    geopandas.GeoDataFrame: A GeoDataFrame containing the combined geometry of the specified county.
    """
    
    # Load mso county TIGER shapefile
    mso_county = gpd.read_file("vector_data/montana_TIGER/tl_2022_30_tabblock20/tl_2022_30_tabblock20.shp")

    # Filter for the specified county FIPS code
    filtered_county = mso_county[(mso_county['COUNTYFP20'] == fips_code)]
    combined_county = filtered_county.dissolve(by='COUNTYFP20')
    return combined_county

mso_county = load_county_geometry('063')
