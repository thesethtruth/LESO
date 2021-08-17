# wind_etri.py

import pandas as pd
import numpy as np


## ETRI 2014
ref_2013_e = 1.4 # M€/MWp
etri_values = pd.DataFrame(
    data=np.array([
    [1800, 1700, 1700],
    [1300, 1200, 1100],
    [1000, 900, 800],
    ]).T,
    index = ['2030', "2040", "2050"],
    columns = ["High", "Ref.", "Low"]
) # data from table 4, page 16
cf_ref_2013_e = 23
capacity_factor = [35, 40, 45]

etri_values = etri_values/1000
etri_factors = etri_values/ref_2013_e

#%% plotting

import plotly.graph_objects as go

fig = go.Figure()
fig.update_layout(template='simple_white')


fig.add_trace(go.Scatter(
    x=list(etri_factors.index) + list(etri_factors.index)[::-1],
    y=list(etri_factors.High) + list(etri_factors.Low)[::-1],
    fill='toself',
    fillcolor= '#8cc0ed',
    line_color= 'rgba(0,0,0,0)',
    showlegend=True,
    name='uncertainty range',    
    opacity=0.4
))

fig.add_trace(go.Scatter(
    x=list(etri_factors.index), 
    y=list(etri_factors['Ref.']), 
    line_color= '#8cc0ed',
    mode='lines+markers',
    name='center values',    
    opacity=1
))



fig.update_xaxes(title='years', range=[2030, 2050])
fig.update_yaxes(title='cost factor', range=[0.5, 1.4])
fig.show()

# %%
