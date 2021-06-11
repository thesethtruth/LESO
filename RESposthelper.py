# RESpost-helper.py
from numpy import column_stack, row_stack
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

def make_installed_capacity_chart(ndf, colors):
    
    tndf = ndf.transpose()

    fig = go.Figure(data=[

        go.Bar(
            name=tech, 
            x=row.index, 
            y=row.values,
            marker = dict(
                color=colors[i],
                opacity=global_alpha))
            
            for i, (tech, row) in enumerate(tndf.iterrows())

    ])
    
    fig.update_yaxes(visible=False)

    fig.update_layout(
        barmode='group',
        paper_bgcolor = 'rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_orientation = "h",
        margin= global_margins
        )
    
    
    return fig

def extract_plotting_specs(data, whitelist=['pv','wind','lith','hy']):

    ckeys = [ckey for ckey in data.keys() 
                if 
                any([x in ckey for x in whitelist])]

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
    
    labels = extract_labels(ckeys)
    colors = extract_colors(ckeys)

    return labels, colors