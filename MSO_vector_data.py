import geopandas
import matplotlib.pyplot as plt
import rasterio

# Load shapefiles
roads = geopandas.read_file('vector_data/TIGER/tl_2021_30063_roads.shp')
natural = geopandas.read_file('vector_data/mso_county2/shape/natural.shp')
waterways = geopandas.read_file('vector_data/mso_county2/shape/waterways.shp')

# Load raster


fig, ax = plt.subplots(figsize=(10, 10))
roads.plot(ax = ax, color = 'black', linewidth = 0.5)
natural.plot(ax=ax, color="brown", alpha=0.5)
waterways.plot(ax=ax, color="blue", linewidth=0.5)
plt.show()














#### Troble plotting roads.shp
# roads = geopandas.read_file('vector_data/mso_county2/shape/roads.shp')
# buildings = geopandas.read_file('vector_data/mso_county2/shape/buildings.shp')
# landuse = geopandas.read_file('vector_data/mso_county2/shape/landuse.shp')
# natural = geopandas.read_file('vector_data/mso_county2/shape/natural.shp')
# waterways = geopandas.read_file('vector_data/mso_county2/shape/waterways.shp')

# fig, ax = plt.subplots(figsize=(10, 10))
# roads.plot(ax=ax, color="black", linewidth=0.5)
# buildings.plot(ax=ax, color="gray", alpha=0.5)
# landuse.plot(ax=ax, color="green", alpha=0.5)

# plt.show()



# waterways.plot()
# plt.show()


# roads = roads[~roads['type'].isin(['unclassified', 'track', 'pedestrian', 'service'])]

# roads.plot()
# plt.show()









# roads_simplified = roads[~roads['type'].isin(['pedestrian','footway','path','steps','track','trunk','unclassified'])]

# # Plot filtered roads


# roads.to_crs(epsg=3857, inplace=True)
# extreme_geometries = roads[roads.geometry.length > 10]  # Adjust threshold
# roads = roads[~roads.index.isin(extreme_geometries.index)]
# roads.plot()
# plt.show()

# roads = roads[roads.geometry.length < 10]

# # Adjust threshold
# # Find and plot geometries with extreme lengths or coordinates
# extreme_geometries = roads[roads.geometry.length > 10]  # Adjust threshold
# extreme_geometries.plot(color="blue")  # Plot suspected outliers
# plt.show()

# extreme_geometries.head

# roads_simplified.plot()
# plt.show()

# land.crs
# roads = roads.simplify(tolerance=0.001, preserve_topology=True)

# land.plot()
# rivers.plot()



# invalid_geometries = roads[~roads.is_valid]
# print(invalid_geometries)