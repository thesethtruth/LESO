# quickbrowser.py
from LESO.attrdict import AttrDict
from LESO.experiments.analysis import load_ema_leso_results
import appfunctions as af

import json
import dash
from dash import dcc
from pathlib import Path
from dash.dependencies import Input, Output
from dash import html
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(
    __name__, external_stylesheets=external_stylesheets, title="LESO results browser"
)

FOLDER = Path(r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\thesis scripts\experiments\2030\results")
*_, df = load_ema_leso_results(
    run_id=210924, 
    exp_prefix='gld2030',
    results_folder=FOLDER)

app.layout = html.Div(
    [
        html.H3("Results quick browsing analysis"),
        dcc.Markdown("Select a **primary** feature to filter:"),
        dcc.Dropdown(
            id="filter-select-A",
            options=[
                {"label": key, "value": key}
                for key in df.columns if df[key].dtype == 'float64'
            ],
            value=df.columns[0],
            persistence=True,
        ),
        dcc.RangeSlider(
            id="filter-slider-A",
            persistence=False,
        ),
        html.P(id="filter-callback-A"),
        dcc.Markdown("Select a **secondary** feature to filter:"),
        dcc.Dropdown(
            id="filter-select-B",
            options=[
                {"label": key, "value": key}
                for key in df.columns if df[key].dtype == 'float64'
            ],
            value=df.columns[0],
            persistence=True,
        ),
        dcc.RangeSlider(
            id="filter-slider-B",
            persistence=False,
        ),
        html.P(id="filter-callback-B"),
        dcc.Graph(id="filter-fig"),
        html.P("Select a simulation run"),
        dcc.Dropdown(
            id="filtered-experiment-select",
            persistence=True,
        ),
        html.P("Select a component to assess"),
        dcc.Dropdown(
            id="selected-component",
            value=None,
            persistence=False,
        ),
        dbc.Table(id="component-table"),
        dcc.Graph(id="hourly"),
        html.P(
            ["Browse through the year per weeknumber below:"],
            style={"padding-left": "5%"},
        ),
        dcc.Slider(
            id="startingweek",
            min=min(af.weeks.values()),
            max=max(af.weeks.values()),
            value=af.startingweek,
            persistence=False,
        ),
        dcc.Store(
            id="data-store",
            data=dict(),
        ),
        dcc.Store(
            id="store-filtered-df",
            data=dict(),
        ),
    ],
    className="container",
)

## reads associated JSON file and stores to react app
## (this allows for sharing between callbacks)
@app.callback(
    Output("data-store", "data"),
    Input("filtered-experiment-select", "value"),
)
def data_store(selected_model):

    if selected_model is None:
        ...
    else:
        with open(selected_model) as json_file:
            data = json.load(json_file)
        return data

## Filter A
@app.callback(
    Output("filter-slider-A", "min"),
    Output("filter-slider-A", "max"),
    Output("filter-slider-A", "value"),
    Output("filter-slider-A", "marks"),
    Output("filter-slider-A", "step"),
    Input("filter-select-A", "value"),
)
def filter_a(feature):
    minn = df[feature].min()
    maxx = df[feature].max()
    value = [minn, maxx]
    marks = {i: str(round(i,2)) for i in value}
    step = (maxx - minn)/100
    return minn, maxx, value, marks, step

## Filter B
@app.callback(
    Output("filter-slider-B", "min"),
    Output("filter-slider-B", "max"),
    Output("filter-slider-B", "value"),
    Output("filter-slider-B", "marks"),
    Output("filter-slider-B", "step"),
    Input("filter-select-B", "value"),
)
def filter_a(feature):
    minn = df[feature].min()
    maxx = df[feature].max()
    value = [minn, maxx]
    marks = {i: str(round(i,2)) for i in value}
    step = (maxx - minn)/100
    return minn, maxx, value, marks, step

## Slider A
@app.callback(
    Output("filter-callback-A", "children"),
    Input("filter-slider-A", "value"),
)
def slider_callback(value):
    value = [round(val,3) for val in value]
    return f"Selected values {value}"
## Slider B
@app.callback(
    Output("filter-callback-B", "children"),
    Input("filter-slider-B", "value"),
)
def slider_callback(value):
    value = [round(val,3) for val in value]
    return f"Selected values {value}"

# visualize the filter
@app.callback(
    Output("filter-fig", "figure"),
    Output("store-filtered-df", "data"),
    Input("filter-select-A", "value"),
    Input("filter-select-B", "value"),
    Input("filter-slider-A", "value"),
    Input("filter-slider-B", "value"),
)
def filter_figure(x_col, y_col, x_range, y_range):
    
    xmin, xmax = x_range
    ymin, ymax = y_range
    
    x_slice = (df[x_col] > xmin) & (df[x_col] < xmax)
    y_slice = (df[y_col] > ymin) & (df[y_col] < ymax)
    total_slice = x_slice & y_slice
    sliced_df = df[total_slice]
    fig = go.Figure(data=px.scatter(
        sliced_df,
        x=x_col,
        y=y_col
    )
    )
    fig.update_layout(
        template="simple_white"
        )
    fig.update_xaxes(range=(df[x_col].min()*1.05, df[x_col].max()*1.05))
    fig.update_yaxes(range=(df[y_col].min()*1.05, df[y_col].max()*1.05))

    data = df.to_json()
    return fig, data

## populate dropdown based on selection
@app.callback(
    Output("filtered-experiment-select", "options"),
    Output("filtered-experiment-select", "value"),
    Input("filter-select-A", "value"),
)
def populate_filtered_experiments(data):
    
    p = Path(r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\thesis scripts\experiments\2030\results")
    filenames = {str(pi.stem): p / pi for pi in p.glob("*.json")}
    options=[
        {"label": key, "value": str(value.absolute())}
        for key, value in filenames.items()
    ]
    # value= options[0]["value"]
    value = None
    print(len(options))
    return options, value

## hourly profile plot
@app.callback(
    Output("hourly", "figure"),
    Input("startingweek", "value"),
    Input("data-store", "data"),
)
def profile_plot(startingweek, data):

    fig = af.make_profile_plot(startingweek, data)

    return fig


## component browser dropdown populator
@app.callback(Output("selected-component", "options"), Input("data-store", "data"))
def component_dropdown(data):
    data = AttrDict(data)
    name = lambda key: data.components[key]["name"] + f" ({key})"
    options = [{"label": name(key), "value": key} for key in data.components.keys()]
    options.insert(0, {"label": "None", "value": "null"})

    return options

## component table callback
@app.callback(
    Output("component-table", "children"),
    Input("filtered-experiment-select", "value"),
    Input("data-store", "data"),
)
def component_table(ckey, data):

    table = af.make_component_table(ckey, data)

    return table

if __name__ == "__main__":
    app.run_server(debug=True)
