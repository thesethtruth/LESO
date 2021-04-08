# Dash related
from dash import Dash
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash

# Other packages
from geopy.geocoders import Nominatim



geolocator = Nominatim(user_agent='locator-for-dash-app')


app = Dash(prevent_initial_callbacks=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    html.Div([
        html.P('Insert location search string'),
        dcc.Input(
            id = 'location-input',
            type = 'text',
            debounce = True
            ),
        dbc.Button(
            'Search',
            id = 'search-button',
            color = 'secondary',
            size  = 'lg',
            )
        ]),
    dl.Map([dl.TileLayer(), dl.LayerGroup(id="layer")],
           id="map", style={'width': '20%', 'height': '50vh', 'margin': "auto", "display": "block"}),
    html.P(id = 'coordinates-display'),
])


@app.callback(
    Output("layer", "children"), 
    Output("coordinates-display", "children"),
    Input("search-button", "n_clicks"),
    Input("map", "click_lat_lng"),
    Input("location-input", "value"),
)
def map_click(clicks, click_lat_lng, search_input):
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    empty = search_input == None 

    if not empty and 'search-button' in changed_id:
        
        location = geolocator.geocode(search_input)
        if location == None:
            marker, location_string = None, 'Failed to find location based on search input'
        else:
            search_lat_long = [location.latitude, location.longitude]
            location_string = "Selected location: ({:.3f}, {:.3f})".format(*search_lat_long)
            marker = [dl.Marker(position=search_lat_long, children=dl.Tooltip(location_string))]
            
    elif not click_lat_lng == None:
        
        location_string = "Selected location: ({:.3f}, {:.3f})".format(*click_lat_lng)
        marker = [dl.Marker(position=click_lat_lng, children=dl.Tooltip(location_string))]

    return marker, location_string


if __name__ == '__main__':
    app.run_server(debug = True)