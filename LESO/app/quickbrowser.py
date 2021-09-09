# quickbrowser.py
import appfunctions as af

import json
import dash
from pathlib import Path
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(
    __name__, external_stylesheets=external_stylesheets, title="LESO results browser"
)

FOLDER = Path(r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\thesis scripts\experiments\evhub\results")

app.layout = html.Div(
    [
        html.H3("Results quick browsing analysis"),
        html.P("Select a simulation run"),
        dcc.Dropdown(
            id="selected-model",
            options=[
                {"label": key, "value": value}
                for key, value in af.load_component_options(FOLDER).items()
            ],
            value=list(af.load_component_options(FOLDER).values())[0],
            persistence=False,
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
    ],
    className="container",
)

## reads associated JSON file and stores to react app
## (this allows for sharing between callbacks)
@app.callback(
    Output("data-store", "data"),
    Input("selected-model", "value"),
)
def data_store(selected_model):

    if selected_model is None:
        ...
    else:
        with open(selected_model) as json_file:
            data = json.load(json_file)
        return data


## hourly profile plot
@app.callback(
    Output("hourly", "figure"),
    Input("startingweek", "value"),
    Input("data-store", "data"),
)
def profile_plot(startingweek, data):

    fig = af.make_profile_plot(startingweek, data)

    return fig


## second figure callback
@app.callback(
    Output("figure-2", "figure"),
    Output("figure-2-title", "children"),
    Input("data-store", "data"),
    Input("selected-figure-2", "value"),
)
def figure2(data, selected_fig):
    if selected_fig is not None:

        fig_factory = af.figure_2_options[selected_fig]["function"]
        fig = fig_factory(data)
        title = af.figure_2_options[selected_fig]["display-text"]

        return fig, title


## component browser dropdown populator
@app.callback(Output("selected-component", "options"), Input("data-store", "data"))
def component_dropdown(data):

    name = lambda key: data[key]["name"] + f" ({key})"
    options = [{"label": name(key), "value": key} for key in data.keys()]
    options.insert(0, {"label": "None", "value": "null"})

    return options


## component table callback
@app.callback(
    Output("component-table", "children"),
    Input("selected-component", "value"),
    Input("data-store", "data"),
)
def component_table(ckey, data):

    table = af.make_component_table(ckey, data)

    return table


if __name__ == "__main__":
    app.run_server(debug=True)
