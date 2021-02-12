import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import dash_table
from plotly.subplots import make_subplots


# default values for DOFs
defaultcharger = 3
## battery size is default set to the minimum value of corresponding selected amount of chargers, unless defined by user

# define color scales
colordict = {
        # Powers
        'PV power': '#ebd25b',
        'Wind power': '#8cc0ed',
        'Battery discharging':  '#7fc78f',
        'Grid import':'#f2b65c',
        'Underload': '#f25c5c',
        # Loads
        'Consumption load': '#f5645f',
        'Charging load': '#a5c0c2',
        'Battery charging': '#85a0d6',
        'Grid export': '#d18426',
        'Curtailment': '#454545',
        # Sinks
        'Battery energy': '#85a0d6',
        'Battery SOC': '#f25c5c'
    }
# define linewidth
linewidth = 0.3

# # read timeseries
# filepath = "outputdata/timeseries_1000.0kWh_3chargers.pkl"
# timeseries = pd.read_pickle(filepath)
# timeseries = timeseries/1e3         # kWh

# # read yearly
# filepath = "outputdata/yearly_1000.0kWh_3chargers.pkl"
# yearly = pd.read_pickle(filepath)
# yearly = yearly/1e6         # kWh

# read financials
# filepath = "outputdata/financials_1000.0kWh_3chargers.pkl"
# financials = pd.read_pickle(filepath)


# read performance indicators
filepath = "outputdata/performanceindicators.pkl"
pi = pd.read_pickle(filepath)

# options for initialize
optionframe = pd.read_csv("outputdata/optionframe.csv", index_col = 0)
chargeroptions = optionframe.drop_duplicates(subset= ['Chargers'])['Chargers']


# options for dropdown menu
weeks = {}
for i in range(1,53) :
    weeks['Week {:.0f}'.format(i)] = i
startingweek = list(weeks.values())[0]


# dropdown menu
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
            html.H3("Initialize model"),
            html.Div([
            html.P("Select number of chargers"),
            dcc.Slider(
                id='selected-charger',
                min = min(chargeroptions),
                max = max(chargeroptions),
                step = None,
                marks={value:"{} chargers".format(value) for value in chargeroptions},
                value= defaultcharger,
                persistence=True
            ),
            html.Br(),
            'Select corresponding battery storage capacity [kWh]',
            html.Div(dcc.Slider(id='selected-battery'), id='battery-container'),
            html.Br(),
            ]),
            html.Div([
            html.H3("Time-series analysis"),
            dcc.Graph(id="hourly"),
            html.P('Browse through the year per weeknumber below:'),
            dcc.Slider(
                id='startingweek',
                min = min(weeks.values()),
                max = max(weeks.values()),
                step = None,
                marks = {value:"{}".format(value) for value in weeks.values()},
                value= startingweek,
                persistence=True
            ),
            dcc.Graph(id="weekly")
                    ]),
            html.Div([
            html.H3('Design section'),
            html.P('Plot this primary performance indicator'),
            dcc.Dropdown(
                id= 'selected-PI1',
                options = [{'label': k, 'value':k}
                            for k in pi.columns[2:]],
                value = pi.columns[2],
                persistence = True
            ),
            html.P('Plot this secondary performance indicator'),
            dcc.Dropdown(
                id= 'selected-PI2',
                options = [{'label': k, 'value':k}
                            for k in pi.columns[2:]],
                value = pi.columns[3],
                persistence = True
            ),
            html.P('While keeping this DOF constant'),
            dcc.Dropdown(
                id= 'selected-variable',
                options = [{'label': k, 'value':k}
                            for k in pi.columns[:2]],
                value = pi.columns[0],
                persistence = True
            ),
            dcc.Graph(id="design-plot"),
            ]),
            html.Div([
            html.H3('Tabulated data of selected design') #,
            # dash_table.DataTable(
            #     id ='finance-table',
            #     columns=[{"name": i, "id": i} 
            #              for i in financials.columns],
            #     data = financials.to_dict(orient='records'),
            #     style_cell=dict(textAlign='left'),
            #     )
            ])    
])

# styling options
layoutstyling = dict(
    paper_bgcolor  = 'white' ,
    )




## corresponding battery size
@app.callback(
    Output('battery-container', 'children'),
    Input('selected-charger', 'value')
)
def set_battery(charger):
    correspondingbatteries = optionframe[optionframe['Chargers']==charger].iloc[:,1].values
    return dcc.Slider(
        id='selected-battery',
        min = min(optionframe[optionframe['Chargers']==charger].iloc[:,1].values),
        max = max(optionframe[optionframe['Chargers']==charger].iloc[:,1].values),
        step = None,
        marks={int(value):"{} kWh".format(value) for value in correspondingbatteries},
        value= min(optionframe[optionframe['Chargers']==charger].iloc[:,1].values),
        persistence= True
    )

## weekly plot on hourly resolution
@app.callback(
    Output("hourly", "figure"), 
    Input("startingweek", "value"),
    Input('selected-battery', 'value'), 
    Input('selected-charger', 'value')
)
def hourly(startingweek, battery, charger):
    start = (startingweek-1)*168
    end = startingweek*168
    if battery == None:
        battery = min(optionframe[optionframe['Chargers']==charger].iloc[:,1].values)
    selectedoption = "{battery}.0kWh_{charger}chargers.pkl".format(battery = battery, charger = charger)
    # read timeseries
    filepath = "outputdata/{datatype}_{selectedoption}".format(selectedoption = selectedoption, datatype = 'timeseries')
    timeseries = pd.read_pickle(filepath)
    timeseries = timeseries/1e3         # kWh
    fig = go.Figure()
    # powers
    for label in timeseries.columns[0:5]:
        fig.add_trace(go.Scatter(
            x= timeseries.index[start:end],
            y= timeseries[label].iloc[start:end],
            stackgroup = 'power',
            mode = 'lines',
            line = dict(width = linewidth, color = colordict[label]),
            name = label
            ))
    # loads
    for label in timeseries.columns[5:10]:
        fig.add_trace(go.Scatter(
            x= timeseries.index[start:end],
            y= timeseries[label].iloc[start:end],
            stackgroup = 'load',
            mode = 'lines',
            line = dict(width = linewidth, color = colordict[label]),
            name = label
            ))
    fig.update_layout(
        title ="Total energy balance in week {startingweek} on hourly resolution".format(startingweek = startingweek),
        xaxis_title="Day of the year",
        yaxis_title="Hourly power [KWh/h]"
        )
    return fig

## yearly plot on weekly resolution
@app.callback(
    Output("weekly", "figure"),
    Input('selected-battery', 'value'), 
    Input('selected-charger', 'value')
)
def weekly(battery, charger):
    fig = go.Figure()
    if battery == None:
        battery = min(optionframe[optionframe['Chargers']==charger].iloc[:,1].values)
    selectedoption = "{battery}.0kWh_{charger}chargers.pkl".format(battery = battery, charger = charger)
    # read timeseries
    filepath = "outputdata/{datatype}_{selectedoption}".format(selectedoption = selectedoption, datatype = 'yearly')
    yearly = pd.read_pickle(filepath)
    yearly = yearly/1e6         # MWh
    # powers
    for label in yearly.columns[0:5]:
        fig.add_trace(go.Scatter(
            x= yearly.index,
            y= yearly[label],
            stackgroup = 'power',
            mode = 'lines',
            line = dict(width = linewidth, color = colordict[label]),
            name = label
            ))
    # loads
    for label in yearly.columns[5:10]:
        fig.add_trace(go.Scatter(
            x= yearly.index,
            y= yearly[label],
            stackgroup = 'load',
            mode = 'lines',
            line = dict(width = linewidth, color = colordict[label]),
            name = label
            ))
    fig.update_layout(
        title ="Total energy balance of the whole year on weekly average resolution",
        xaxis_title="Week of the year",
        yaxis_title="Average weekly energy [MWh]"
        )
    return fig

## design plot
@app.callback(
    Output("design-plot", "figure"),
    Input('selected-PI1', 'value'), 
    Input('selected-PI2', 'value'),
    Input('selected-variable', 'value'),
    Input('selected-battery', 'value'), 
    Input('selected-charger', 'value')
)
def designplot(pisel1, pisel2, variable, battery, charger):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if variable == "Chargers": # Selected constant chargers, variable battery capacity
        selectedpi1 = pi[pi[variable]== charger][pisel1]
        selectedpi2 = pi[pi[variable]== charger][pisel2]
        selectedvar = pi[pi[variable]== charger]["Battery capacity"]
        
        dofvar = 'Battery capacity'
        constantvar = battery
        constantpi1 = pi[pi[variable]==charger][pi[pi[variable]==charger]['Battery capacity']==battery][pisel1]
        constantpi2 = pi[pi[variable]==charger][pi[pi[variable]==charger]['Battery capacity']==battery][pisel2]
    
    else: # Selected constant battery capacity, variable chargers
        selectedpi1 = pi[pi[variable]== battery][pisel1]
        selectedpi2 = pi[pi[variable]== battery][pisel2]
        selectedvar = pi[pi[variable]== battery]["Chargers"]

        dofvar = 'Number of chargers'
        constantvar = charger 
        constantpi1 = pi[pi[variable]==battery][pi[pi[variable]==battery]['Chargers']==charger][pisel1]
        constantpi2 = pi[pi[variable]==battery][pi[pi[variable]==battery]['Chargers']==charger][pisel2]

    markercolor = 'crimson'
    markerdict = dict(
            size = 25,
            color = markercolor,
            opacity = 0.3,
            symbol = 'hourglass',
            line = dict(
                width = 1,
                color = markercolor)

        )

    # <<-------- left axis

    # continuum
    fig.add_trace(go.Scatter(
            x = selectedvar.values,
            y = selectedpi1.values,
            mode = 'lines+markers',
            name = pisel1,
            
        ),
    secondary_y=False,)

    # Selected option (constant)
    fig.add_trace(go.Scatter(
            x = [constantvar],
            y = constantpi1.values,
            mode = 'markers',
            name = " ".join([pisel1,"of current set-up"]),
            marker = markerdict,            
        ),
    secondary_y=False,)




    # ------->> right axis

    # continuum
    fig.add_trace(go.Scatter(
            x = selectedvar.values,
            y = selectedpi2.values,
            mode = 'lines+markers',
            name = pisel2,
        ),
    secondary_y=True,)

    # Selected option (constant)
    fig.add_trace(go.Scatter(
            x = [constantvar],
            y = constantpi2.values,
            mode = 'markers',
            name = " ".join([pisel2,"of current set-up"]),
            marker = markerdict,          
        ),
    secondary_y=True,)


    fig.update_layout(
    title ="{} vs. {} over {}".format(pisel1, pisel2.lower(), dofvar.lower()),
    xaxis_title= dofvar,
    plot_bgcolor  = 'white', 
    )

    fig.update_yaxes(title_text=pi.iloc[-1][pisel1], secondary_y=False)
    fig.update_yaxes(title_text=pi.iloc[-1][pisel2], secondary_y=True)
    return fig


# if __name__ == "__main__":
#    app.run_server(debug=True)
