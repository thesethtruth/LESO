from LESO.plotly_extension import lighten_color
import pandas as pd
import numpy as np
import plotly.graph_objects as go


## Fraunhofer 2015 Current and Future Cost of Photovoltaics
ref_2015_f = 1 # M€/MWp
fraunhofer = { 
    "2030": [0.7547738693467337, 0.5537688442211057], 
    "2040": [0.6743718592964826, 0.38492462311557796],
    "2050": [0.606030150753769, 0.27939698492462317]
} # data from figure 42, page 53

fraunhofer_factors = pd.DataFrame(fraunhofer.values(), index = fraunhofer.keys(), columns=['Fraunhofer high', 'Fraunhofer low'])
fraunhofer_values = fraunhofer_factors*ref_2015_f
fraunhofer_factors['Fraunhofer ref.'] = fraunhofer_factors.mean(axis=1)

## ETRI 2014
ref_2014_e = 0.98 # M€/MWp
etri = { 
    "2030": [720, 520], 
    "2040": [650, 470],
    "2050": [580, 420]
} # data from table 7, page 20
cf_ref_2014_e = 13
capacity_factors = [16, 17, 17]


etri14_values = pd.DataFrame(etri.values(), index = etri.keys(), columns=['ETRI high', 'ETRI low'])
etri14_values['ETRI ref.'] = [640, 580, 520]
etri14_values = etri14_values/1000
etri14_factors = etri14_values/ref_2014_e


etri_2017 = np.array([
    [720, 580, 500],
    [600, 450, 370],
    [450, 370, 320],
    [390, 310, 260],
    [870, 780, 730]]
).T # data from excel sheet 

etri17_colums = [
    "Baseline",
    "Diversified",
    "ProRES",
    "Min",
    "Max",
]
ref_2017_e = 1.02 # M€/MWp
etri17_values = pd.DataFrame(etri_2017, index=etri.keys(), columns=etri17_colums)/1000
etri17_factors = etri17_values/ref_2017_e
#%%
all_factors = pd.concat([etri14_factors, etri17_factors, fraunhofer_factors], axis=1)
outer_factors = pd.DataFrame(index=["2030", "2040", "2050"], columns=['min', 'max'])
outer_factors['min'] = all_factors.min(axis=1)
outer_factors['max'] = all_factors.max(axis=1)

outer_factors = outer_factors.round(2)

from palettable.scientific.sequential import Davos_5 as color
etri14_color = color.hex_colors[-4]
etri17_color = color.hex_colors[-3]
fraunhofer_color = color.hex_colors[-2]

if True:

    fig = go.Figure()
    fig.update_layout(template='simple_white')


    fig.add_trace(go.Scatter(
        x=list(etri17_factors.index) + list(etri17_factors.index)[::-1],
        y=list(etri17_factors.Min) + list(etri17_factors.Max)[::-1],
        fill='toself',
        fillcolor= lighten_color(etri17_color, 0.5),
        line_color= 'rgba(0,0,0,0)',
        showlegend=True,
        name='ETRI 2017 range',    
    ))

    fig.add_trace(go.Scatter(
        x=list(fraunhofer_factors.index) + list(fraunhofer_factors.index)[::-1],
        y=list(fraunhofer_factors["Fraunhofer high"]) + list(fraunhofer_factors['Fraunhofer low'])[::-1],
        fill='toself',
        fillcolor= lighten_color(fraunhofer_color, 0.5),
        line_color= 'rgba(0,0,0,0)',
        showlegend=True,
        name='Fraunhofer 2015 range',    
    ))

    fig.add_trace(go.Scatter(
        x=list(etri14_factors.index) + list(etri14_factors.index)[::-1],
        y=list(etri14_factors['ETRI high']) + list(etri14_factors['ETRI low'])[::-1],
        fill='toself',
        fillcolor= lighten_color(etri14_color, 0.5),
        line_color= 'rgba(0,0,0,0)',
        showlegend=True,
        name='ETRI 2014 range',    
    ))

    for col in fraunhofer_factors.columns:
        fig.add_trace(go.Scatter(
            x=list(fraunhofer_factors.index), 
            y=list(fraunhofer_factors[col]),
            line_color= fraunhofer_color,
            line_dash= None if "high" in col or "low" in col else'dot',
            mode='lines+markers',
            name='ETRI 2014 baseline',
            showlegend= False if "high" in col or "low" in col else True,    
            opacity=1
        ))


    for col in etri14_factors.columns:
        fig.add_trace(go.Scatter(
            x=list(etri14_factors.index), 
            y=list(etri14_factors[col]),
            line_color= etri14_color,
            line_dash= None if "high" in col or "low" in col else'dot',
            mode='lines+markers',
            name='ETRI 2014 baseline',
            showlegend= False if "high" in col or "low" in col else True,    
            opacity=1
        ))


    for col in etri17_factors.columns:
        fig.add_trace(go.Scatter(
            x=list(etri17_factors.index), 
            y=list(etri17_factors[col]),
            line_color= etri17_color,
            line_dash= None if "Min" in col or "Max" in col else'dot',
            mode='lines+markers',
            name=f'ETRI 2017 {col}',
            showlegend= False if "Min" in col or "Max" in col else True,    
            opacity=1
        ))
    # fig.update_traces(mode='lines')

    fig.update_yaxes(title='projected cost factor', range=[0, 1])

    from LESO.plotly_extension import thesis_default_styling
    fig = thesis_default_styling(fig)
    fig.update_layout(width=800)
    
    if False:
        fig.write_image("pv.pdf")
    else:
        fig.show()