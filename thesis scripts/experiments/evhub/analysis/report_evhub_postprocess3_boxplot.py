# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt


from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from evhub_postprocess_tools import (
    get_data_from_db,
    gcloud_read_experiment,
    pv_col,
    wind_col,
    bat2_col,
    bat6_col,
    bat10_col,
    total_bat_col,
    batcols,
    bivar_tech_dict,
)

#%% paths
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
LEFT_MARGIN = 0.15
COLLECTION = "evhub"
RUN_ID = "2210_v2"

#%% load in results
db = get_data_from_db(collection=COLLECTION, run_id=RUN_ID, force_refresh=False)
db.rename({"clusters_from_gridcap": "clusters"}, axis=1, inplace=True)
#%% start the plots

tech_dict = {"PV": pv_col, "wind": wind_col, "battery": total_bat_col}

for tech, col in tech_dict.items():
    if tech == "battery":
        unit = "MWh"
    else:
        unit = "MW"
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
    fig.set_size_inches(6, 1.5)

    sns.boxplot(
        x=col,
        y="grid_capacity",
        data=db,
        ax=ax,
        orient="h",
        palette="dark:#69d_r",
    )

    ax.set_ylabel("grid capacity (MW)")
    ax.set_xlabel(f"{tech} deployed capacity ({unit})")

    default_matplotlib_save(fig, IMAGE_FOLDER / f"report_evhub_boxplot_{tech}.png")

#%% boxplot with hue clusters

db = pd.read_pickle(RESOURCE_FOLDER / "evhub_2210_v2_clustered.pkl")
db.rename({"clusters_from_gridcap": "clusters"}, axis=1, inplace=True)

for tech, col in tech_dict.items():
    if tech == "battery":
        unit = "MWh"
    else:
        unit = "MW"
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
    fig.set_size_inches(6, 2)

    sns.boxplot(
        x=col,
        y="grid_capacity",
        data=db,
        hue="clusters",
        ax=ax,
        orient="h",
        palette="mako",
    )

    ax.get_legend().remove()
    ax.set_ylabel("grid capacity (MW)")
    ax.set_xlabel(f"{tech} deployed capacity ({unit})")

    default_matplotlib_save(
        fig, IMAGE_FOLDER / f"report_evhub_boxplot_{tech}_clusters.png",
    )


# %%
if input("Crop the images in this folder? [y/n]") == "y":
    from LESO.plotting import crop_transparency_top_bottom
    crop_transparency_top_bottom(
        folder_to_crop=IMAGE_FOLDER,
        file_ext_to_crop="png",
        override_original=True
    ) 