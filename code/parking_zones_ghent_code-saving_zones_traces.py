# =============================================================================
# # Set-up
# =============================================================================
import requests
import pandas as pd
import numpy as np
import geopandas as gpd

import plotly.express as px
# Ensure plots are shown in browser
import plotly.io as pio
pio.renderers.default='browser' # set browser as renderer

import json

# # Render dash app
# import dash
# from dash import dcc
# from dash import html


# =============================================================================
# Downloading geojson file and loading it
# =============================================================================

url = "https://data.stad.gent/api/explore/v2.1/catalog/datasets/parkeertariefzones-gent/exports/geojson?lang=nl&timezone=Europe%2FBrussels"
response = requests.get(url)

# if response.status_code == 200:
#     # Save the GeoJSON content to a file
#     with open("../data/parkeertariefzones-gent.geojson", "wb") as file:
#         file.write(response.content)
#     print("GeoJSON file downloaded successfully.")
# else:
#     print(f"Failed to download GeoJSON file. Status code: {response.status_code}")


# Load GeoDataFrame from GeoJSON file
gdf = gpd.read_file('../data/parkeertariefzones-gent.geojson')

# =============================================================================
# Modify geojson to remove overlapping small zones 
# (i.e. tiny red zone in the middle of large red zone)
# and merge adjacent zones
# =============================================================================

# Create 'dissolved_gdf' to contain the larger areas without the smaller 
# enclosed ones using column 'zone' to determine whether zones should be dissolved.
dissolved_gdf = gdf.dissolve(by='zone')


# Reset the index to get new GeoDataFrame with a default index
dissolved_gdf = dissolved_gdf.reset_index()

# =============================================================================
# # Merge 'Blauwe zone speciaal' with 'Blauwe zone' and 'Groene zone uitbreiding'
# # with 'Groene zone' since they involve the same parking regime. 
# =============================================================================

# Define function to perform merging
def merge_and_drop_zones(gdf, source_zone, target_zone):
    # Extract the geometry of the source zone
    geometry_to_merge = gdf[gdf['zone'] == source_zone]['geometry'].iloc[0]

    # Find the index of the target zone
    index_to_merge_into = gdf[gdf['zone'] == target_zone].index[0]

    # Merge the geometries
    gdf.at[index_to_merge_into, 'geometry'] = gdf.at[index_to_merge_into, 'geometry'].union(geometry_to_merge)

    # Drop the row corresponding to the source zone
    gdf = gdf[gdf['zone'] != source_zone]
    
    # Reset the index to get new GeoDataFrame with a default index
    gdf = gdf.reset_index()

    return gdf

# Merge 'Blauwe zone speciaal' with 'Blauwe zone'
dissolved_gdf = merge_and_drop_zones(dissolved_gdf, 'Blauwe zone speciaal', 'Blauwe zone')

# Merge 'Groene zone uitbreiding' with 'Groene zone'
dissolved_gdf = merge_and_drop_zones(dissolved_gdf, 'Groene zone uitbreiding', 'Groene zone')


# # Save the dissolved GeoDataFrame to a new GeoJSON file
dissolved_gdf.to_file('../data/parkeertariefzones-gent_simplified.geojson', driver='GeoJSON')

# =============================================================================
# #Create graph
# =============================================================================


# Define color dict
color_dict = {
    "Rode zone": "red",
    "Oranje zone": "orange",
    "Gele zone": "yellow",
    "Groene zone": "green",
    "Blauwe zone": "blue",
    # "Blauwe zone speciaal": "blue",
    # "Groene zone uitbreiding": "green",
    }

# Create choropleth map
choropleth_map = px.choropleth_mapbox(
    dissolved_gdf,
    geojson=dissolved_gdf.geometry,
    locations=dissolved_gdf.index,  # Use GeoDataFrame index as locations
    color="zone",
    color_discrete_map=color_dict,  # Adjust color as needed
    mapbox_style="carto-positron",
    center={"lat": dissolved_gdf.geometry.centroid.y.mean(), "lon": dissolved_gdf.geometry.centroid.x.mean()},
    zoom=11,
    opacity=0.3,
)
   
# Remove hover labels by setting hovermode to False
choropleth_map.update_layout(hovermode=False)

# Show map
choropleth_map.show()

  
# Store parking zones as traces to later on add to other graphs
traces = []
for index, row in dissolved_gdf.iterrows():
    traces.append(choropleth_map.data[index])

# Save traces to file
traces_filename = '../data/traces.json'
traces_data = [pio.to_json(trace) for trace in traces]
with open(traces_filename, 'w') as traces_file:
    json.dump(traces_data, traces_file)

# # Load traces from file
# # traces_filename = '../data/traces.json'
# with open(traces_filename, 'r') as traces_file:
#     traces_data = json.load(traces_file)

