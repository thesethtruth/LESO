#%% imports
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from functools import cache
import json
import os
import glob
from matplotlib.patches import Patch
#%% Define helperfunctions

@cache
def get_geo_data(url):
    gdf = gpd.read_file(url)
    return gdf

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

#%% import RES data

wd = os.getcwd()
simulations_raw = glob.glob(wd+'/cache/2030*.json')
extractor = lambda x: x.split('\\')[-1].replace(".json", '').replace("2030RES_", '')
simulations_keys = [extractor(x) for x in simulations_raw]

roundd = lambda x: [round(i,1) for i in x]
results = list()
for sim in simulations_raw:
    with open(sim) as infile:
        results.append(json.load(infile))

pv, wind, bat, h2, etm, grid = [], [], [], [], [], []
for res in results:
    for key in res.keys():
        if 'pv' in key:
            pv.append(res[key]['settings']['installed'])
        if 'wind' in key:
            wind.append(res[key]['settings']['installed'])
        if 'lith' in key:
            bat.append(res[key]['settings']['installed'])
        if 'hydro' in key:
            h2.append(res[key]['settings']['installed'])
        if 'dem' in key:
            etm.append(-min(res[key]['state']['power [-]']))
        if 'grid' in key:
            grid.append(res[key]['settings']['installed'])

labels, colors = extract_plotting_specs(results[0])

components = [pv, wind, bat, h2]
components[2] = [el/1.25 for el in components[2]]
components[3] = [el/50 for el in components[3]]
components = [[round(el) for el in comp] for comp in components ]
prod, store = components[:2], components[2:]

#%% configuration

rc = {
    'font.family':'Poppins',
    'font.size': 20
    }
plt.rcParams.update(rc)



#%% find gemeentes within RES
url = "https://opendata.arcgis.com/datasets/6d91187a2f9f4bc589d2c6fb5699d7c0_0.geojson"
res = get_geo_data(url)
_indices = [1, 4, 23, 8, 20, 21]
resgld = res.iloc[_indices]

#%% Plot Netherlands RES
def plot_bar_on_map(variables, colors, labels, title):
    
    fig, ax = plt.subplots(figsize=(10, 10))

    resgld.to_crs(epsg= 3035).plot(
        ax=ax, alpha=1, 
        color='#e8e8e8', edgecolor='#4d4d4d', 
        linewidth=1)

    centroids = resgld.to_crs(epsg= 3035).centroid
    xmin, xmax, ymin, ymax = [*ax.get_xlim(), *ax.get_ylim()]
    dx = xmax - xmin
    dy = ymax - ymin
    width, height = 0.05*dx, 0.13*dy

    plt.axis('off')

    
    for i, point in enumerate(centroids.values):
        ax_bar = ax.inset_axes([point.x-width/2, point.y-height/3, width, height], transform=ax.transData)
        ax_bar.bar(
            range(1, len(variables)+1), 
            [x[i] for x in variables], 
            color = colors)
        ax_bar.set_ylim(ymin=0,ymax=max(max(variables)))
        ax_bar.set_axis_off()
        

    ax.legend(
        handles=[
            Patch(color=color, label=label)
            for label, color in zip(labels, colors)
            ], 
            loc=1)

    plt.title(title)
        


plot_bar_on_map(store, colors[2:], labels[2:], "Storage installed capacity [MW]")
plot_bar_on_map(prod, colors[:2], labels[:2], "VRE production installed capacity [MW]")

# %%
