import glob
import json
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from LESO import System
import dash_bootstrap_components as dbc

# function for reading current possible model runs
def reload_component_options():

    wd = os.getcwd()
    components_raw = glob.glob(wd+'/cache/*.json')
    extractor = lambda x: x.split('\\')[-1].replace("__", ' ').replace("T", ' ').replace(".json", '')
    components = {extractor(x):x for x in components_raw}
    
    return components

# options for dropdown menu
weeks = {}
for i in range(1,53) :
    weeks['Week {:.0f}'.format(i)] = i
startingweek = list(weeks.values())[0]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets,
                title= 'Quick browser'
                )

app.layout = html.Div([
            html.H3("Results quick browsing analysis"),
            html.P("Select a simulation run"),
            dcc.Dropdown(
                id= 'selected-model',
                options = [{'label': key, 'value': value}
                            for key, value in reload_component_options().items()],
                value = None,
                persistence = True
            ),
            dcc.Graph(id="hourly"),
            html.P(['Browse through the year per weeknumber below:'
                ], style= {"padding-left": "5%"}),
            dcc.Slider(
                id='startingweek',
                min = min(weeks.values()),
                max = max(weeks.values()),
                value= startingweek,
                persistence=False
            ),
            dbc.Button(
                "Reload model results", 
                outline=True, 
                color="dark",
                id = 'reload-model'),
            dcc.Store(id='components-store'),
], className= "container")


# styling options
layoutstyling = dict(
    paper_bgcolor  = 'white' ,
    )

# plotting function
def scatter_power(fig, start, end, serie, group, label, color):
    fig.add_trace(go.Scatter(
        x= serie.index[start:end],
        y= serie.iloc[start:end]/1e3,
        stackgroup = group,
        mode = 'lines',
        name = label,
        line = dict(width = 0.3, color = color),
        ))

@app.callback(
    Output("components-store", "data"),
    Input("reload-model", "n_clicks"),
)
def reloader(n):
    if n:
        components = reload_component_options()
    
        return components

## weekly plot on hourly resolution
@app.callback(
    Output("hourly", "figure"), 
    Input("startingweek", "value"),
    Input("selected-model", "value"),
)
def hourly(startingweek, selected_model):
    start = (startingweek-1)*168
    end = startingweek*168
    fig = go.Figure()
    if selected_model is None:
        ...
    else:
        with open(selected_model) as json_file:
            data = json.load(json_file)
            sdict = data['system']
        
        for ckey in data.keys():
            
            if ckey == 'system':
                break
            cdict = data[ckey]

            _df = pd.DataFrame(cdict['state'], index = sdict['dates'])
            _df.index = _df.index = pd.to_datetime(_df.index)
            
            pos_serie = getattr(_df, 'power [+]', None)
            neg_serie = getattr(_df, 'power [-]', None)


            if pos_serie is not None:
                if not pos_serie.sum() < 1e-5:
                    styling = cdict['styling']
                    styling = styling[0] if isinstance(styling, list) else styling 
                    column = 'power [+]'
                    label = styling['label'] + f' ({ckey})'
                    group = styling['group']
                    color = styling['color']
                    scatter_power(fig, start, end, pos_serie, group, label, color)

            if neg_serie is not None:
                if not neg_serie.sum() > -1e-5:
                    styling = cdict['styling']
                    styling = styling[1] if isinstance(styling, list) else styling
                    column = 'power [-]'
                    label = styling['label'] + f' ({ckey})'
                    group = styling['group']
                    color = styling['color']
                    scatter_power(fig, start, end, neg_serie, group, label, color)

    fig.update_layout(
        title ="Total energy balance in <b>week {startingweek}</b> on hourly resolution".format(startingweek = startingweek),
        xaxis_title="Day of the year",
        yaxis_title="Hourly power [KWh/h]",
        plot_bgcolor  = 'white',
        )
    return fig

if __name__ == "__main__":
   app.run_server(debug=True)