import requests
import plotly.graph_objs as go
import pandas as pd



# Fetching data from the API
url = "https://data.stad.gent/api/explore/v2.1/catalog/datasets/bezetting-parkeergarages-real-time/records?limit=20"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    # print(data)
    
    df = pd.DataFrame(data["results"])
    print(df)
    
    names = [entry['fields']['name'] for entry in data['records']]
    available_capacity = [entry['fields']['availablecapacity'] for entry in data['records']]
    total_capacity = [entry['fields']['totalcapacity'] for entry in data['records']]
    occupation = [entry['fields']['occupation'] for entry in data['records']]

    # Create a Plotly figure
    fig = go.Figure()

    # Add traces to the figure
    fig.add_trace(go.Bar(x=names, y=available_capacity, name='Available Capacity', marker_color='green'))
    fig.add_trace(go.Bar(x=names, y=occupation, name='Occupation', marker_color='blue'))
    fig.add_trace(go.Bar(x=names, y=total_capacity, name='Total Capacity', marker_color='orange'))

    # Update layout
    fig.update_layout(
        title='Parking Data',
        xaxis=dict(title='Parking Locations'),
        yaxis=dict(title='Capacity'),
        barmode='group'
    )

    # Display the Plotly figure
    fig.show()
else:
    print("Failed to fetch data")
