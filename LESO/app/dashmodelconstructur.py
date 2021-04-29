import dash
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import dash_table
from plotly.subplots import make_subplots
from LESO import System
import dash_bootstrap_components as dbc
from copy import deepcopy as copy

# open model!
import LESO
system = LESO.System(52, 5, model_name='GUI')


# options for slider
weeks = {}
for i in range(1,53) :
    weeks['Week {:.0f}'.format(i)] = i
startingweek = list(weeks.values())[0]

# define linewidth
linewidth = 0.3

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets,
                title= 'LESO'
                )

app.layout = html.Div([
            html.H3("Add component to energy system"),
                html.Div([
                    dcc.Dropdown(
                        id= 'add-component-dropdown',
                        options = [
                            {'label': key, 'value': key} for key in LESO.ComponentClasses                
                            ],
                        value = list(LESO.ComponentClasses.keys())[0],
                        className = 'four columns',
                    ),
                    dcc.Input(
                        id = 'add-component-input',
                        type = 'text',
                        maxLength = 20,
                        className = 'four columns',
                        required = True,
                        placeholder = 'Input a name',
                    ),
                    dbc.Button(['Add component'],
                        id='add-component-button',
                        style = {'background-color': 'darkgray'},
                        className = 'four columns', 
                        n_clicks=0,
                    ),
                ], className = 'row'),
                html.Br(),
            html.H4(id='system-name'),
            dbc.Table(id='system-overview-table'),
            html.H3("Set  up components"),
            dcc.Dropdown(
                id = 'config-dropdown',
                options = [
                    {'label': component.__str__()+f" ({component.name})", 'value': index}
                    for index, component in enumerate(system.components)
                    ]
            ),
            html.Div(id ='config-table'),
            html.H3("Optimization quick browsing analysis"),
            dbc.Button(
                "Reset model", 
                outline=True, 
                color="dark",
                id = 'reset-model',
                style= {'background-color': 'orangered', 'color': 'white'}),
            html.Div(id='hidden-div', style={'display':'none'}),
], className= "container")



### ADD COMPONENTS
@app.callback(
    Output("system-name", "children"),
    Output("system-overview-table", "children"),
    Output("add-component-input", "value"),
    Input("add-component-button", "n_clicks"),
    Input("reset-model", "n_clicks"),
    State("add-component-dropdown", "value"),
    State("add-component-input", "value"),
)

def reloader(add, reset, key, name):
    
    if name is not None and add:
        if len(name)>2:
            system.add_components([
                LESO.ComponentClasses[key](name)
                ])
    
    df = pd.DataFrame(
            data = {
                'Component ID': [component.__str__() for component in system.components],
                'Component name': [component.name for component in system.components],
                },
            )
    table = dbc.Table.from_dataframe(df, borderless=True, hover=True)

    system.info(print_it=True)
    return system.name, table, ""

### POPULATE CONFIGURATION DROPDOWN
@app.callback(
    Output('config-dropdown', 'options'),
    Input("add-component-button", "n_clicks"),
    Input("reset-model", "n_clicks"),
)
def update_dropdown(add, reset):
    options = [
        {'label': component.__str__()+f" ({component.name})", 'value': index}
        for index, component in enumerate(system.components)
        ]
    return options

### CONFIGURATION TABLE
@app.callback(
    Output('config-table', 'children'),
    Input("config-dropdown", "value"),
    Input("add-component-button", "n_clicks"),
    Input("reset-model", "n_clicks"),
)
def update_dropdown(selected_index, add, reset):
    
    if selected_index is not None:
        defaults = copy(system.components[selected_index].default_values)
        defaults.pop('styling', None)
        defaults.pop('merit_tag', None)
        df = pd.DataFrame({
            "Component property": [key for key in defaults.keys()],
            "Property value" :  [value for value in defaults.values()],
        }
        )

        table = html.Div([
                dash_table.DataTable(
                    columns=[
                        {"name": df.columns[0], "id": df.columns[0], "editable": False},
                        {"name": df.columns[1], "id": df.columns[1], "editable": True},
                    ],
                    data= df.to_dict('records')
                )], style = {'visibility': 'visible'}
                
            )
        return table
    else:
        
        table = html.Div([
                ], style = {'visibility': 'hidden'}
        )

        return table
        


### RESET
@app.callback(
    Output("hidden-div", "children"),
    Input("reset-model", "n_clicks"),
)

def reset(n):
    global system
    system = LESO.System(52, 5, model_name='Model GUI reset')
    


if __name__ == "__main__":
   app.run_server(debug=True)

