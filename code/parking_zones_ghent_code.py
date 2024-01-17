#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 09:49:37 2024

@author: niels_tack
"""
# =============================================================================
# # Set-up
# =============================================================================
import requests
import pandas as pd
import numpy as np
import geopandas as gpd

import plotly.express as px
import plotly.graph_objects as go # to create table using graphical objects
# # Ensure plots are shown in browser
# import plotly.io as pio
# pio.renderers.default='browser' # set browser as renderer

# Render dash app
import dash
from dash import dcc
from dash import html


# =============================================================================
# Downloading geojson file and loading it
# =============================================================================

url = "https://data.stad.gent/api/explore/v2.1/catalog/datasets/parkeertariefzones-gent/exports/geojson?lang=nl&timezone=Europe%2FBrussels"
response = requests.get(url)

if response.status_code == 200:
    # Save the GeoJSON content to a file
    with open("../data/parkeertariefzones-gent.geojson", "wb") as file:
        file.write(response.content)
    print("GeoJSON file downloaded successfully.")
else:
    print(f"Failed to download GeoJSON file. Status code: {response.status_code}")


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
# dissolved_gdf.to_file('../data/parkeertariefzones-gent_simplified.geojson', driver='GeoJSON')

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

 


# Create choropleth map with reduced file
fig = px.choropleth_mapbox(
    dissolved_gdf,
    geojson=dissolved_gdf.geometry,
    locations=dissolved_gdf.index,  # Use GeoDataFrame index as locations
    color="zone",
    color_discrete_map=color_dict,  # Adjust color as needed
    mapbox_style="carto-positron",
    center={"lat": dissolved_gdf.geometry.centroid.y.mean(), "lon": dissolved_gdf.geometry.centroid.x.mean()},
    zoom=10,
    opacity=0.3,
)



# # Show the map
# fig.show()


# =============================================================================
# # Create dash app
# =============================================================================
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(children=[
    html.H1("Choropleth Map with Tables"),
    
    # Choropleth map
    dcc.Graph(figure=fig),
    
    # # Tables
    # dcc.Graph(figure=fees_day_table, id='fees_day_table'),
    # dcc.Graph(figure=fees_evening_table, id='fees_evening_table'),
    
    # # Show parking fees for each zone (image from url)
    # html.Img(src="https://stad.gent/sites/default/files/styles/gallery_full/public/media/images/20220531_AV_parkeertarieven_SK.jpg?itok=tgkOsPak",
    #     alt="Parkeertarieven",
    #     style={'width': '40%', 'height': '40%'}  # Adjust the width and height as needed
    # )
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)