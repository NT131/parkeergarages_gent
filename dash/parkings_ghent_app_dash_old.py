#from flask import Flask, render_template

import dash
from dash import html, dcc
from dash.dependencies import Output, Input


import pandas as pd

import plotly.express as px

import requests


import os 
import json
from datetime import datetime

import locale




## Set Belgium time (for Dutch-language indicators of last update time)
#locale.setlocale(locale.LC_TIME, 'nl_BE.utf-8')

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
        with open('../data/fetched_data.json', 'w') as json_file:
            json.dump(filtered_data, json_file)    
    else:
        print("Failed to fetch data")
        
# =============================================================================
# Initialize data and app
# =============================================================================
# Fetch data file if it is not yet present
if not os.path.exists("../data/fetched_data.json"):
    fetch_data()

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
        last_update = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d %B %Y - %H:%M:%S")
        return f"Laatste update: {last_update}"
    else:
        return "Laatste update: onbekend"

# =============================================================================
# Function to update graph
# =============================================================================

def update_graph():
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
        #labels={'availablecapacity': 'Beschikbare parkeerplaatsen'}  # Set the legend label
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

        html.Div(className='d-flex justify-content-between align-items-center flex-wrap', children=[ # Make button and update indicator more compact
            html.Div(id='last-update-time', className='text-center pt-3 pb-2', children=get_last_update_time('../data/fetched_data.json')),
        
            html.Div(className='text-center', children=[
                html.Button("Update", id="refresh-btn", className='btn btn-primary mt-3 mb-3'),
                dcc.Interval(id='refresh-interval-component', interval=10*60*1000, n_intervals=0)
            ]),
        ]),
        
        html.Div(className='graph-container custom-graph-container', children=[ # Add custom-graph-container next to standard Bootstrap CSS style
            dcc.Graph(id='live-update-graph', figure=update_graph()),
            dcc.Interval(id='update-graph-interval', interval=1*1000, n_intervals=0)
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
    Input('refresh-btn', 'n_clicks')
)
def update_data(interval_n, btn_n):
    if interval_n > 0 or btn_n is not None:
        fetch_data()  # Fetch data if interval or button triggered
        
        # Read the updated JSON file
        with open('../data/fetched_data.json', 'r') as json_file:
            data = json.load(json_file)
        df = pd.DataFrame(data) # Transform to DataFrame for easier handling
        
        # Update last update time content after fetching data
        last_update_time = get_last_update_time('../data/fetched_data.json')
        
        return True, 0, update_graph(), last_update_time
    
    return True, 0, update_graph(), dash.no_update  # If no updates, prevent changing the last-update-time

# =============================================================================
# Run app
# =============================================================================

# Define a callable application object for Gunicorn
application = app.server


if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0', port=5001)
