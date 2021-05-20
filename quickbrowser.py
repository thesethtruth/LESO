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
import dash_bootstrap_components as dbc
from copy import deepcopy as copy
import dash_table

# function for reading current possible model runs (doesnt work!)
def reload_component_options():

    wd = os.getcwd()
    components_raw = glob.glob(wd+'/cache/*.json')
    extractor = lambda x: x.split('\\')[-1].replace(".json", '')
    components = {extractor(x):x for x in components_raw}
    
    return components

# options for dropdown menu
weeks = {}
for i in range(1,53):
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
                persistence = False
            ),
            html.P("Select a component to assess"),
            dcc.Dropdown(
                id = 'selected-component',
                value = None, 
                persistence = False,
            ),
            dbc.Table(id='component-table'),
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
            dcc.Graph(id="pie-chart"),
            dbc.Button(
                "Do not press", 
                outline=True, 
                color="dark",
                id = 'reload-model'),
            dcc.Store(
                id='data-store',
                data = dict(),
            ),
], className= "container")


# styling options
layoutstyling = dict(
    paper_bgcolor  = 'white' ,
    )

# plotting functions
def scatter_power(fig, start, end, serie, group, label, color):
    fig.add_trace(go.Scatter(
        x= serie.index[start:end],
        y= serie.iloc[start:end]/1e3,
        stackgroup = group,
        mode = 'lines',
        name = label,
        line = dict(width = 0.3, color = color),
        ))
    
def make_pie_chart(data):
    
    fig = make_subplots(
                    rows=1, cols=2, 
                    specs=[[{'type':'domain'}, {'type':'domain'}]],
                    subplot_titles=['Supply by source', 'Demand by source']
                )
    
    ckeys = [ckey for ckey in data.keys() if ckey != 'system']

    summer = lambda ckey, tag : sum(data[ckey]['state'][tag])
    
    def extract_labels(ckeys, pos):
        labels = list()
        for ckey in ckeys:
            i = 0 if pos else 1
            styling = data[ckey]['styling']
            styling = styling[i] if isinstance(styling, list) else styling 
            labels.append(styling['label'])
        return labels
    
    def extract_colors(ckeys, pos):
        
        colors = list()
        for ckey in ckeys:
            i = 0 if pos else 1
            styling = data[ckey]['styling']
            styling = styling[i] if isinstance(styling, list) else styling 
            colors.append(styling['color'])
        return colors


    powers ={  
        ckey: summer(ckey, 'power [+]') 
        for ckey in ckeys
        if summer(ckey, 'power [+]') > 1
    }
        
    loads = {
        ckey: -summer(ckey, 'power [-]') 
        for ckey in ckeys 
        if summer(ckey, 'power [-]') < -1
    }

    fig.add_trace(go.Pie(
                    values = list(powers.values()),
                    labels = extract_labels(powers.keys(), True),
                    marker_colors = extract_colors(powers.keys(), True),
                    name="Supply by source"), 
                    1, 1)

    fig.add_trace(go.Pie(
                    values = list(loads.values()),
                    labels = extract_labels(loads.keys(), False),
                    marker_colors = extract_colors(loads.keys(), False),
                    name="Demand by source"), 
                    1, 2)
    fig.update(
        layout_title_text='Yearly energy supply/demand by source'
    )

    return fig

@app.callback(
    Output("data-store", "data"),
    Input("selected-model", "value"),
)
def reloader(selected_model):

    if selected_model is None:
        ...
    else:
        with open(selected_model) as json_file:
            data = json.load(json_file)
        return data

## weekly plot on hourly resolution
@app.callback(
    Output("hourly", "figure"), 
    Input("startingweek", "value"),
    Input("data-store", "data"),
)
def hourly(startingweek, data):
    start = (startingweek-1)*168
    end = startingweek*168
    fig = go.Figure()
    
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
                label = styling['label'] + f' ({ckey})'
                group = styling['group']
                color = styling['color']
                scatter_power(fig, start, end, pos_serie, group, label, color)

        if neg_serie is not None:
            if not neg_serie.sum() > -1e-5:
                styling = cdict['styling']
                styling = styling[1] if isinstance(styling, list) else styling
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

# second figure callback
@app.callback(
    Output("pie-chart", "figure"), 
    Input("data-store", "data"),
)
def figure2(data):

    fig = make_pie_chart(data)
    
    return fig

# dropdown populator
@app.callback(
    Output("selected-component", "options"),
    Input("data-store", "data")
)
def component_dropdown(data):

    name = lambda key: data[key]['name'] + f' ({key})'
    options = [{'label': name(key), 'value': key}
                for key in data.keys()]

    return options

# component table callback
@app.callback(
    Output("component-table","children"),
    Input("selected-component","value"),
    Input("data-store", "data"),
)
def component_table(ckey, data):
    ckey = None if not ckey in data.keys() else ckey 
    if ckey is not None:
        cdict = data[ckey]
        if ckey == 'system':
            cdict = copy(data[ckey])
            cdict.pop('dates', None)
        else:
            cdict = copy(data[ckey]['settings'])
            cdict.pop('styling', None)
        
        df = pd.DataFrame({
            "Component property": [key for key in cdict.keys()],
            "Property value" :  [value for value in cdict.values()],
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
        
    else:
        table = html.Div([
                ], style = {'visibility': 'hidden'}
        )
    
    return table




if __name__ == "__main__":
   app.run_server(debug=True)