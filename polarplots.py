import plotly.express as px
import os
import glob
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from durationcurves import kotzur_normalize
from scipy.signal import savgol_filter

# df = px.data.wind()


wd = os.getcwd()
simulations_raw = glob.glob(wd + "/results/2030*.json")
filename = simulations_raw[0]

with open(filename) as infile:
    d = json.load(infile)
components = list(d["components"].keys())

fig = go.Figure()

for key in components:
    if 'hy' not in key:
        cols = ['pos', 'neg', 'energy']
        component = d["components"][key]
        df = pd.DataFrame(component["state"])
        df.columns = [cols[i] for i,col in enumerate(df.columns)]
        
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
                mode='lines',
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
