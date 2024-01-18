#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 14:22:50 2024

@author: niels_tack
"""

import dash
from dash import html, dcc
from dash.dependencies import Output, Input

import geopandas as gpd

import pandas as pd

import plotly.express as px

import requests


import os 
import json
from datetime import datetime

import locale

# Set Belgium time (for Dutch-language indicators of last update time)
locale.setlocale(locale.LC_TIME, 'nl_BE.utf-8')

# =============================================================================
# Fetch data
# =============================================================================

# Fetching data function
def fetch_data():
    url = "https://data.stad.gent/api/explore/v2.1/catalog/datasets/bezetting-parkeergarages-real-time/records?limit=20"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()    
        # Filter out the row with name "Loop"
        filtered_data = [record for record in data.get("results", []) if record.get("name") != "The Loop"]
        
		# Write new data to file
        with open('../data/fetched_data.json', 'w') as json_file:
            json.dump(filtered_data, json_file)  
		

		# Get the current time and update time file
        current_time = datetime.now().strftime("%d %B %Y - %H:%M:%S")
        with open('../data/last_update.txt', 'w') as update_file:
            update_file.write(current_time)
		
    else:
        print("Failed to fetch data")
        
# =============================================================================
# Initialize data and app
# =============================================================================
# Fetch data
	### OPTION 1 ###
	# Fetch data file if it is not yet present
if not os.path.exists("../data/fetched_data.json"):
    fetch_data()
	### OPTION 2 ###
	# Fetch data again on each time opening webpage
#fetch_data()



# Initialize the Dash app
app = dash.Dash(__name__, 
		url_base_pathname='/visualisaties/parkeergarages-gent/',
		assets_folder='assets') # Relative path to the folder of css file)
app.title = "Beschikbaarheid parkeergarages Gent"

# # run the data fetch file if not yet done (i.e. no csv present)
# if not os.path.exists("../data/fetched_data.csv"):
#     # Run the data_fetch.py file to fetch the data
#     os.system('python3 data_fetch.py')

# Perform initial read-in of the filtered JSON file
with open('../data/fetched_data.json', 'r') as json_file:
    data = json.load(json_file)
# Transform to dataframe for easier handling
df = pd.DataFrame(data)


# =============================================================================
# # Function to get the last modification time of the JSON file
# =============================================================================

def get_last_update_time(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as update_file:
            last_update = update_file.read().strip()
        return f"Laatste update: {last_update}"
    else:
        return "Laatste update: onbekend"

# =============================================================================
# Function to update graph
# =============================================================================

def update_parkings():
    # Create a hovertemplate
    hover_template = "<b>%{hovertext}</b><br>" + \
                     "Beschikbare plaatsen: %{customdata[1]}<br>" + \
                     "Totaal aantal plaatsen: %{marker.size}"
    
    # Create a map figure using Plotly Express
    fig = px.scatter_mapbox(
        df,
        lat=df["location"].apply(lambda x: x['lat']),
        lon=df["location"].apply(lambda x: x['lon']),
        color="availablecapacity",
        size="totalcapacity",
        hover_name="name",
        hover_data={"name": True, "availablecapacity": True},
        # Create predefined color scale to ensure sufficient contrast, not coming close to white
        color_continuous_scale=[
            [0.0, "red"],
            [0.3, "orange"],
            [0.5, "yellow"],
            [0.7, "lime"],
            [1.0, "green"]
        ],
        # color_continuous_scale="RdYlGn",  # Red (low available capacity) to Green (high available capacity)
        range_color=[df["availablecapacity"].min(), df["availablecapacity"].max()],
        # For mapbox_styles, see https://plotly.com/python/mapbox-layers/ 
        mapbox_style="carto-positron", # light
        # mapbox_style="carto-darkmatter", # dark
        # mapbox_style="open-street-map", # street style
        zoom=12,
        # labels={'availablecapacity': 'Beschikbare parkeerplaatsen'}  # Set the legend label
    )
    
    # Update hovertemplate
    fig.update_traces(
        hovertemplate=hover_template
    )
    
    # Set the custom data for hovertemplate
    fig.update_traces(customdata=df[['name', 'availablecapacity', 'totalcapacity']].values)
    
    
    # Update the layout to hide the color scale legend (shows bad on mobile site)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
		coloraxis_showscale=False,
        )
    
    return fig

def formatting_parkings(fig, hover_template):
    # Update hovertemplate
    fig.update_traces(
        hovertemplate=hover_template
    )
    
    # Set the custom data for hovertemplate
    fig.update_traces(customdata=df[['name', 'availablecapacity', 'totalcapacity']].values)
    
    
    # Update the layout to hide the color scale legend (shows bad on mobile site)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
		coloraxis_showscale=False,
        )
    
    return fig

# =============================================================================
# Function to update trace (parking zones)
# =============================================================================
# Load GeoDataFrame from GeoJSON file
dissolved_gdf = gpd.read_file('../data/parkeertariefzones-gent_simplified.geojson')



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
parking_zones_map = px.choropleth_mapbox(
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
parking_zones_map.update_layout(hovermode=False)

# =============================================================================
# Define app layout
# =============================================================================

# Define the app layout, using CSS Bootstrap
app.layout = html.Div([
    html.Link(rel='stylesheet', href='assets/styles.css'),  # Your custom CSS link
    html.Link(rel='stylesheet', href='https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'),  # Bootstrap CSS link

    html.Div(className='container mt-4', children=[
        html.H1(className='text-center', children="Beschikbaarheid parkeergarages Gent"),

        html.P(className='text-center', children="Beschikbaarheid van de verschillende parkeergarages binnen het Gentse stadscentrum."),

        html.Div(className='graph-container custom-graph-container', children=[ # Add custom-graph-container next to standard Bootstrap CSS style
            
            # Dropdown for selecting display option
            dcc.Dropdown(
                id='display-option',
                options=[
                    {'label': 'Parkeergarages', 'value': 'parkings'},
                    {'label': 'Parkeertariefzones', 'value': 'parking-zones'},
                    {'label': 'Parkeergarages en parkeertariefzones', 'value': 'parkings_parking-zones'},
                ],
                value='parkings',  # Set default value
                multi=False  # Allow only one option to be selected
            ),
            # Graph                                                                 
            dcc.Graph(id='live-update-graph', figure=update_parkings()),
            dcc.Interval(id='update-graph-interval', interval=1*1000, n_intervals=0),
            


        ]),        

        html.Div(className='d-flex justify-content-between align-items-center flex-wrap', children=[ # Make button and update indicator more compact
            html.Div(id='last-update-time', className='text-center pt-3 pb-2', children=get_last_update_time('../data/last_update.txt')),
        
            html.Div(className='text-center', children=[
                html.Button("Update", id="refresh-btn", className='btn btn-primary mt-3 mb-3'),
                dcc.Interval(id='refresh-interval-component', interval=10*60*1000, n_intervals=0)
            ]),
        ]),
        


        html.Footer(className='text-center', children=html.P([
            "De gegevens zijn beschikbaar via ",
            html.A("Stad Gent API", href="https://data.stad.gent/explore/dataset/bezetting-parkeergarages-real-time/table/?sort=-occupation"),
            ". De onderliggende code is beschikbaar op ",
            html.A("GitHub", href="https://github.com/NT131/parkeergarages_gent"),
            "."
        ]))
    ])
])


# =============================================================================
# Callback
# =============================================================================

@app.callback(
    Output('refresh-interval-component', 'disabled'),
    Output('refresh-interval-component', 'n_intervals'),
    Output('live-update-graph', 'figure'),
    Output('last-update-time', 'children'),  # Output to update last-update-time Div
    Input('refresh-interval-component', 'n_intervals'),
    Input('refresh-btn', 'n_clicks'),
    Input('display-option', 'value')  # New input for display option
)
def update_data(interval_n, btn_n, display_option):
    fetch_data()
    
    # Read the updated JSON file
    with open('../data/fetched_data.json', 'r') as json_file:
        data = json.load(json_file)
    df = pd.DataFrame(data)
    
    # Update last update time content after fetching data
    last_update_time = get_last_update_time('../data/last_update.txt')
    
    # Create graph with parking garages
    parkings_map = update_parkings()
    
    
    if display_option == 'parkings':
        return True, 0, parkings_map, last_update_time
    elif display_option == 'parking-zones':
        return True, 0, parking_zones_map, last_update_time  # An empty trace
    elif display_option == 'parkings_parking-zones':
        # Combine the two graphs using add_traces
        combined_fig = parkings_map.add_traces(parking_zones_map['data'])
        return True, 0, combined_fig, last_update_time
    else:
        return True, 0, parkings_map, last_update_time  # Default to showing the graph


# =============================================================================
# Run app
# =============================================================================
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)


