# appfunctions.py
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import dash_html_components as html
import dash_table

import glob
import os
import pandas as pd
from copy import deepcopy as copy

# define it once, use it 9999
global_alpha = 0.8
global_hole = 0.4
global_margins = dict(l=20, r=20, t=20, b=40)

def make_profile_plot(startingweek, data):
    
    start = (startingweek-1)*168
    end = startingweek*168
    fig = go.Figure()
    
    sdict = data['system']
    for ckey in data.keys():

        if ckey == 'system':
            break
        cdict = data[ckey]

        _df = pd.DataFrame(cdict['state'], index = sdict['dates'])
        _df.index = pd.to_datetime(_df.index)
        
        pos_serie = getattr(_df, 'power [+]', None)
        neg_serie = getattr(_df, 'power [-]', None)

        if pos_serie is not None:
            if not pos_serie.sum() < 1e-5:
                styling = cdict['styling']
                styling = styling[0] if isinstance(styling, list) else styling 
                label = styling['label'] + f' ({ckey})'
                group = styling['group']
                color = styling['color']
                make_scatter_power(fig, start, end, pos_serie, group, label, color)

        if neg_serie is not None:
            if not neg_serie.sum() > -1e-5:
                styling = cdict['styling']
                styling = styling[1] if isinstance(styling, list) else styling
                label = styling['label'] + f' ({ckey})'
                group = styling['group']
                color = styling['color']
                make_scatter_power(fig, start, end, neg_serie, group, label, color)

    fig.update_layout(
        title ="Total energy balance in <b>week {startingweek}</b> on hourly resolution".format(startingweek = startingweek),
        xaxis_title="Day of the year",
        yaxis_title="Hourly power [KWh/h]",
        plot_bgcolor  = 'white',
        )
    
    return fig


def make_capex_pie(data):
    
    fig = go.Figure()
    
    ckeys = [ckey for ckey in data.keys() if ckey != 'system']

    def calc_capex(ckey):
        
        cdict = data[ckey]['settings']

        installed = cdict.get('installed', 0)
        unit_capex = cdict.get('capex', 0)
        capex = installed*unit_capex / 1e3
        capex = round(capex,1)
        return capex
    
    def extract_labels(ckeys):
        labels = list()
        for ckey in ckeys:
            labels.append(data[ckey]['name'])
        return labels
    
    def extract_colors(ckeys):
        
        colors = list()
        for ckey in ckeys:
            i = 0
            styling = data[ckey]['styling']
            styling = styling[i] if isinstance(styling, list) else styling 
            colors.append(styling['color'])
        return colors


    CAPEX ={  
        ckey: calc_capex(ckey) 
        for ckey in ckeys
        if calc_capex(ckey)  > 1
    }

    fig.add_trace(go.Pie(
                    values = list(CAPEX.values()),
                    labels = extract_labels(CAPEX.keys()),
                    marker_colors = extract_colors(CAPEX.keys()),
                    name="CAPEX by component",
                    opacity = global_alpha,
                    hole = global_hole), 
                    )

    fig.update_traces(textinfo='percent+value')
    fig.update_layout(
        legend_orientation = "h",
        margin= global_margins
    )

    title = 'CAPEX by component [k€]'

    return fig

def make_energy_pie(data):
    
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
                    name="Supply by source",
                    opacity = global_alpha,
                    hole = global_hole), 
                    1, 1)

    fig.add_trace(go.Pie(
                    values = list(loads.values()),
                    labels = extract_labels(loads.keys(), False),
                    marker_colors = extract_colors(loads.keys(), False),
                    name="Demand by source",
                    opacity = global_alpha,
                    hole = global_hole), 
                    1, 2)

    title = 'Yearly energy supply/demand by source'

    fig.update_layout(
        legend_orientation = "h",
        margin= global_margins
    )

    return fig

def make_energy_over_year(data):
    
    fig = make_subplots(
                    rows=2, cols=1, 
                    subplot_titles=['Supply', 'Demand'],
                    shared_xaxes=True,
                    vertical_spacing=0.1
                )
    
    def extract_label(ckey, power: bool):
        i = 0 if power else 1
        styling = data[ckey]['styling']
        styling = styling[i] if isinstance(styling, list) else styling
        name = data[ckey]['name']
        label = styling['label'] + f" ({name})"
        return label
    
    def extract_color(ckey, power: bool):
        i = 0 if power else 1
        styling = data[ckey]['styling']
        styling = styling[i] if isinstance(styling, list) else styling 
        color = styling['color']
        return color
    
    def create_scatter(df, power: bool, row):
        for column in df.columns:
            fig.add_trace(go.Scatter(
                            x = df.index,
                            y = df[column].values,
                            name = extract_label(column, power),
                            mode="lines",
                            stackgroup='one',
                            groupnorm = 'percent',
                            line = dict(
                                width = 1, 
                                color = extract_color(column, power)),
                            ), 
                            row, 1)

    ckeys = [ckey for ckey in data.keys() if ckey != 'system']
    
    monthdates = pd.to_datetime(data['system']['dates'])
    months = monthdates.month_name().values

    getter = lambda ckey, tag : data[ckey]['state'][tag]
    summer = lambda ckey, tag : sum(data[ckey]['state'][tag])
    
    tag = 'power [+]'
    powers ={  
        ckey: getter(ckey, tag) 
        for ckey in ckeys
        if summer(ckey, tag) > 1
    }
    powers.update({'months':months})
    pdf = pd.DataFrame(powers)
    pdf = pdf.groupby('months',sort=False).sum()
    
    create_scatter(pdf, True, 1)
    
    tag = 'power [-]'
    loads ={  
        ckey: getter(ckey, tag) 
        for ckey in ckeys
        if summer(ckey, tag) < -1
    }
    loads.update({'months':months})
    ldf = pd.DataFrame(loads)
    ldf = ldf.groupby('months',sort=False).sum()

    create_scatter(ldf, False, 2)

    for annotation in fig['layout']['annotations']: 
            annotation['textangle']=-90
            annotation['x']=0
            annotation['xanchor'] = 'right'
            annotation['yanchor'] = 'top'
            annotation['xshift'] = -20


    fig.update_layout(
        legend_orientation = "h",
        margin= dict(l=50, r=20, t=20, b=40),
        plot_bgcolor  = 'white',
    )

    return fig

def make_scatter_power(fig, start, end, serie, group, label, color):
    fig.add_trace(go.Scatter(
        x= serie.index[start:end],
        y= serie.iloc[start:end]/1e3,
        stackgroup = group,
        mode = 'lines',
        name = label,
        line = dict(width = 0.3, color = color),
        ))

def make_component_table(ckey, data):
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

# function for reading current possible model runs (only runs on startup)
def load_component_options():

    wd = os.getcwd()
    components_raw = glob.glob(wd+'/cache/*.json')
    extractor = lambda x: x.split('\\')[-1].replace(".json", '')
    components = {extractor(x):x for x in components_raw}
    
    return components

# options for slider
weeks = {}
for i in range(1,53):
    weeks['Week {:.0f}'.format(i)] = i
startingweek = list(weeks.values())[0]

# figure function map  
figure_2_options = {
    'energy_pie_chart': {'function': make_energy_pie, 'display-text': 'Yearly energy supply/demand by source'},
    'capex_pie_chart': {'function': make_capex_pie, 'display-text': 'CAPEX per component'},
    'energy_per_month': {'function': make_energy_over_year, 'display-text': 'Monthly energy supply/demand by source'},
}

