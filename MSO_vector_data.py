import geopandas
import matplotlib.pyplot as plt
import rioxarray
import xarray as xr
import cartopy.crs as ccrs

# Load shapefiles
roads = geopandas.read_file('vector_data/TIGER/tl_2021_30063_roads.shp')
natural = geopandas.read_file('vector_data/mso_county2/shape/natural.shp')
waterways = geopandas.read_file('vector_data/mso_county2/shape/waterways.shp')

# Load raster
raster = rioxarray.open_rasterio("raster_images/merged_reprojected.tif")

# Reproject shapefiles to match raster
raster_crs = raster.rio.crs
roads = roads.to_crs(raster_crs)
natural = natural.to_crs(raster_crs)
waterways = waterways.to_crs(raster_crs)

fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": ccrs.PlateCarree()})
raster.plot(ax=ax, robust=True, transform=ccrs.PlateCarree())
roads.plot(ax=ax, color="red", linewidth=0.5, label="Roads")
waterways.plot(ax=ax, color="blue", linewidth=0.5, label = "Rivers")
natural.plot(ax=ax, edgecolor="black", linewidth=1, label = "Natural Features")

# Add gridlines and labels
gl = ax.gridlines(draw_labels=True, crs=ccrs.PlateCarree(), alpha=0.5)
gl.top_labels = False
gl.right_labels = False

# Add a title and show the plot
ax.set_title("Reprojected Mosaic with Geographical Context")
plt.show()

