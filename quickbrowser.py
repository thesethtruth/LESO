import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import dash_table
from plotly.subplots import make_subplots
from LESO import System

# open model!
system = System.from_pickle('LESO model')
components = system.components

# options for dropdown menu
weeks = {}
for i in range(1,53) :
    weeks['Week {:.0f}'.format(i)] = i
startingweek = list(weeks.values())[0]

# define color scales


# define linewidth
linewidth = 0.3

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets,
                title= 'Quick browser'
                )

app.layout = html.Div([
            html.H3("Optimization quick browsing analysis"),
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
], className= "container")


# styling options
layoutstyling = dict(
    paper_bgcolor  = 'white' ,
    )

def scatter_power(fig, start, end, component, styling, column):
    fig.add_trace(go.Scatter(
        x= component.state.index[start:end],
        y= component.state[column].iloc[start:end],
        stackgroup = styling['group'],
        mode = 'lines',
        name = styling['label'],
        line = dict(width = 0.3, color = styling['color']),
        ))

## weekly plot on hourly resolution
@app.callback(
    Output("hourly", "figure"), 
    Input("startingweek", "value"),
)
def hourly(startingweek):
    start = (startingweek-1)*168
    end = startingweek*168
    fig = go.Figure()
    
    for component in components:
        _df = component.state

        plot_pos = hasattr(_df, 'power [+]')
        plot_neg = hasattr(_df, 'power [-]')
        plot_power = hasattr(_df, 'power') and not (plot_neg or plot_pos)

        if plot_pos:
            styling = component.styling[0]
            column = 'power [+]'
            scatter_power(fig, start, end, component, styling, column)

        if plot_neg:
            styling = component.styling[1]
            column = 'power [-]'
            scatter_power(fig, start, end, component, styling, column)
        
        if plot_power:
            styling = component.styling
            column = 'power'
            scatter_power(fig, start, end, component, styling, column)

    fig.update_layout(
        title ="Total energy balance in <b>week {startingweek}</b> on hourly resolution".format(startingweek = startingweek),
        xaxis_title="Day of the year",
        yaxis_title="Hourly power [KWh/h]",
        plot_bgcolor  = 'white',
        )
    return fig

if __name__ == "__main__":
   app.run_server(debug=True)