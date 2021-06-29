import plotly.express as px
import os
import glob
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# df = px.data.wind()


wd = os.getcwd()
simulations_raw = glob.glob(wd + "/results/2030*.json")
filename = simulations_raw[0]

with open(filename) as infile:
    d = json.load(infile)
components = list(d["components"].keys())

fig = go.Figure()

for key in components:
    cols = ['pos', 'neg', 'energy']
    component = d["components"][key]
    df = pd.DataFrame(component["state"])
    df.columns = [cols[i] for i,col in enumerate(df.columns)]

    df.index = pd.date_range(start='01/01/2021', periods=8760, freq='h')
    df = df.groupby(df.index.day+df.index.month).mean()
    
    if isinstance(component['styling'], list):
        color = component['styling'][0]['color']
    else:
        color = component['styling']['color']

    r = df['pos']
    theta = df.index/len(df.index)*360

    fig.add_trace(
        go.Scatterpolar(
            r=r,
            theta=theta,
            line=dict(
                color=color,
                smoothing=1.3,
            ),
            name=key,
            mode='lines+markers',
            opacity=0.4
    ))

fig.update_layout(
    template='plotly_dark',
    showlegend=True
    )
fig.update_polars(
    radialaxis=dict(
        visible=False
    ),
    angularaxis=dict(
        visible=False
    ),
    )
fig.show()
