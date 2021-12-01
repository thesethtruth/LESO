#%% imports
from collections import OrderedDict
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from functools import cache
import json
from pathlib import Path
from matplotlib.patches import Patch


#%%

pv_col = "PV South installed capacity"
wind_col = "Vestas V90 2000 installed capacity"
total_bat_col = "total_battery_energy"
grid_col = "Grid connection installed capacity"

FOLDER = Path(__file__).parent
RESOURCE_FOLDER = FOLDER / "resources"
IMAGE_FOLDER = FOLDER / "images"
IMAGE_FOLDER.mkdir(exist_ok=True)
RESOURCE_FOLDER.mkdir(exist_ok=True)
force_refresh = False


#%% Define helperfunctions


@cache
def get_geo_data(url):
    gdf = gpd.read_file(url)
    return gdf


#%% find gemeentes within RES
if force_refresh:
    print("fetching from opendata.arcgis -- refreshed")
    url = "https://opendata.arcgis.com/datasets/6d91187a2f9f4bc589d2c6fb5699d7c0_0.geojson"
    res = get_geo_data(url)
    _indices = [1, 4, 23, 8, 20, 21]
    gdf = res.iloc[_indices]
    pd.to_pickle(gdf, RESOURCE_FOLDER / "res_shapes.pkl")

else:
    print("reading pickle -- not refreshed")
    gdf = pd.read_pickle(RESOURCE_FOLDER / "res_shapes.pkl")


gdf.Regio = gdf.Regio.apply(
    lambda x: x
    if not {"Stedendriehoek/cleantechregioi": "Cleantech"}.get(x, None)
    else {"Stedendriehoek/cleantechregioi": "Cleantech"}.get(x, None)
)

fig, ax = plt.subplots(figsize=(5, 5))
rc = {
    "font.family": "Open Sans",
    "font.weight": "bold",
    "font.style": "italic",
    "font.size": 14,
}
plt.rcParams.update(rc)
gdf.to_crs(epsg=3035).simplify(500).plot(
    ax=ax, alpha=1, color="#2F7DA0", edgecolor="#AAD6E5", linewidth=1
)

centroids = gdf.to_crs(epsg=3035).centroid
xmin, xmax, ymin, ymax = [*ax.get_xlim(), *ax.get_ylim()]
dx = xmax - xmin
dy = ymax - ymin
width, height = 0.07 * dx, 0.13 * dy

gdf.sort_values("Regio", inplace=True)
gdf['Regio'] = sorted(['Foodvalley',
 'Noord-Veluwe',
 'Arnhem\nNijmegen',
 'Rivierenland',
 'Cleantech',
 'Achterhoek'])

pos=[
    (0,20),
    (0,20),
    (-0,20),
    (-0,20),
    (-0,20),
    (-0,20),
]

plt.axis("off")
for i, (idx, r) in enumerate(gdf.to_crs(epsg=3035).iterrows()):
    point = centroids[idx]
    region = r['Regio']
    ax_bar = ax.inset_axes(
        [point.x, point.y, 200, 200],
        transform=ax.transData,
    )
    ax_bar.set_axis_off()
    ax_bar.text(*pos[i], region,horizontalalignment='center', color="#123C63")
    ax_bar.text(0,0, ".",horizontalalignment='center', color="#123C63", fontsize=30)


plt.tight_layout(pad=0.3)
plt.savefig(IMAGE_FOLDER / f"report_2030_res_map.png", dpi=300)

