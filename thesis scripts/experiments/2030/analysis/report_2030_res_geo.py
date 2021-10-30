#%% imports
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
    resgld = res.iloc[_indices]
    pd.to_pickle(resgld, RESOURCE_FOLDER / "res_shapes.pkl")

else:
    print("reading pickle -- not refreshed")
    resgld = pd.read_pickle(RESOURCE_FOLDER / "res_shapes.pkl")

#%% Plot Netherlands RES
def plot_bar_on_map(variables, colors, labels, title):

    fig, ax = plt.subplots(figsize=(10, 10))

    resgld.to_crs(epsg=3035).plot(
        ax=ax, alpha=1, color="#e8e8e8", edgecolor="#4d4d4d", linewidth=1
    )

    centroids = resgld.to_crs(epsg=3035).centroid
    xmin, xmax, ymin, ymax = [*ax.get_xlim(), *ax.get_ylim()]
    dx = xmax - xmin
    dy = ymax - ymin
    width, height = 0.05 * dx, 0.13 * dy

    plt.axis("off")

    for i, point in enumerate(centroids.values):
        ax_bar = ax.inset_axes(
            [point.x - width / 2, point.y - height / 3, width, height],
            transform=ax.transData,
        )
        ax_bar.bar(
            range(1, len(variables) + 1), [x[i] for x in variables], color=colors
        )
        ax_bar.set_ylim(ymin=0, ymax=max(max(variables)))
        ax_bar.set_axis_off()

    ax.legend(
        handles=[
            Patch(color=color, label=label) for label, color in zip(labels, colors)
        ],
        loc=1,
    )

    plt.title(title)

    return fig, ax


#%% read data
db = pd.read_pickle(RESOURCE_FOLDER / "gld2030_3010_RES.pkl")
targets = db.target_RE_strategy.unique()
col_map = {pv_col: "PV", wind_col: "wind", total_bat_col: "battery"}
idx_map = {
    "2030RES_Foodvalley ": "Foodvalley",
    "2030RES_NoordVeluwe": "Noord-Veluwe",
    "2030RES_ArnhemNijmegen": "Arnhem Nijmegen",
    "2030RES_Rivierenland": "Rivierenland",
    "2030RES_Cleantech": "Cleantech",
    "2030RES_Achterhoek": "Achterhoek",
}

color = {
    "PV": "#edc645",
    "wind": "steelblue",
    "battery": "darkseagreen",
    "grid": "darkgrey",
}
for target in targets:
    df = db.query(f"target_RE_strategy == '{target}'")
    subdf = df[[pv_col, wind_col, total_bat_col, "scenario"]].copy()
    subdf.set_index("scenario", inplace=True)
    subdf.rename(col_map, inplace=True, axis=1)
    subdf.rename(idx_map, inplace=True, axis=0)
    normed_subdf = subdf / subdf.max()
    print(target)
    for i in subdf.index:
        print(i)
    

# #%%
# fig, ax = plot_bar_on_map(
#     variables=,
#     colors=,
#     labels=,
#     "Storage installed capacity [MW]")
