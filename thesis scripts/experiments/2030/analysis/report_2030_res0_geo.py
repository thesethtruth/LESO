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
    resgld = res.iloc[_indices]
    pd.to_pickle(resgld, RESOURCE_FOLDER / "res_shapes.pkl")

else:
    print("reading pickle -- not refreshed")
    resgld = pd.read_pickle(RESOURCE_FOLDER / "res_shapes.pkl")


resgld.Regio = resgld.Regio.apply(
    lambda x: x
    if not {"Stedendriehoek/cleantechregioi": "Cleantech"}.get(x, None)
    else {"Stedendriehoek/cleantechregioi": "Cleantech"}.get(x, None)
)
resgld.sort_values("Regio", inplace=True)
#%% Plot Netherlands RES
def plot_bar_on_map(df, colors, target: str = None, normed=False):
    if normed:
        normed = "_normed"
    else:
        normed = ""

    fig, ax = plt.subplots(figsize=(5, 5))
    rc = {
        "font.family": "Open Sans",
        "font.size": 10,
    }

    plt.rcParams.update(rc)

    resgld.to_crs(epsg=3035).plot(
        ax=ax, alpha=1, color="#e8e8e8", edgecolor="#4d4d4d", linewidth=1
    )

    centroids = resgld.to_crs(epsg=3035).centroid
    xmin, xmax, ymin, ymax = [*ax.get_xlim(), *ax.get_ylim()]
    dx = xmax - xmin
    dy = ymax - ymin
    width, height = 0.07 * dx, 0.13 * dy

    plt.axis("off")
    labels = df.columns
    for i, point in enumerate(centroids.values):
        ax_bar = ax.inset_axes(
            [point.x - width / 2, point.y - height / 3, width, height],
            transform=ax.transData,
        )
        df.iloc[i, :].plot.bar(color=colors.values(), ax=ax_bar)
        if normed:
            ax_bar.set_ylim([0, 1])
        else:
            ax_bar.set_ylim([0, max(df.max())])
        ax_bar.set_axis_off()

    ax.legend(
        handles=[
            Patch(color=color, label=label)
            for label, color in zip(labels, colors.values())
        ],
        loc=1,
        frameon=False,
        bbox_to_anchor=(0.85, 0.95),
    )

    plt.tight_layout(pad=0.3)
    plt.savefig(IMAGE_FOLDER / f"report_2030_res_mapplot_{target}{normed}.png", dpi=300)
    return fig, ax


#%% read data

db = pd.read_pickle(RESOURCE_FOLDER / "gld2030_3010_RES2.pkl")

targets = db.target_RE_strategy.unique()
#%%
col_map = {pv_col: "PV", wind_col: "wind", total_bat_col: "battery", grid_col: "grid"}

idx_map = {
    "2030RES_Foodvalley ": "Foodvalley",
    "2030RES_NoordVeluwe": "Noord-Veluwe",
    "2030RES_ArnhemNijmegen": "Arnhem Nijmegen",
    "2030RES_Rivierenland": "Rivierenland",
    "2030RES_Cleantech": "Cleantech",
    "2030RES_Achterhoek": "Achterhoek",
}

color = OrderedDict(
    {
        "PV": "#edc645",
        "wind": "steelblue",
        "battery": "darkseagreen",
        "grid": "darkgrey",
    }
)
db.rename(col_map, inplace=True, axis=1)
db = db[["PV", "wind", "battery", "scenario", "grid", "target_RE_strategy"]]
db.set_index("scenario", inplace=True)
db.rename(idx_map, inplace=True, axis=0)
wdb = db.drop("target_RE_strategy", axis=1).copy()
for target in targets:
    subdf = db.query(f"target_RE_strategy == '{target}'").copy()
    subdf.drop("target_RE_strategy", axis=1, inplace=True)
    subdf.sort_index(inplace=True)
    normed_subdf = subdf / wdb.max()
    print(normed_subdf)
    print(target)
    fig, ax = plot_bar_on_map(df=subdf, colors=color, target=target, normed=False)


# #%%
