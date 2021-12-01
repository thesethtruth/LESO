# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


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

#%% start the plots

tech_dict = {"PV": pv_col, "wind": wind_col, "battery": total_bat_col}

fig, axi = plt.subplots(3, 1, figsize=(6, 5))
plt.tight_layout(pad=0.3)
rc = {
    "font.family": "Open Sans",
    "font.size": 10,
    "legend.fontsize": 8,
}
plt.rcParams.update(rc)
plt.subplots_adjust(hspace=0.1)
for ax in axi.flat:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
for i, (tech, col) in enumerate(tech_dict.items()):
    if tech == "battery":
        unit = "MWh"
    else:
        unit = "MW"


    ax=axi[i]
    sns.stripplot(
        x=col,
        y="grid_capacity",
        data=db,
        ax=ax,
        orient="h",
        size=2,
        alpha=0.8,
        jitter=0.5,
        edgecolor="black",
        palette="mako",
    )

    ax.set_ylabel("grid capacity (MW)")
    ax.set_xlabel(f"{tech} deployed capacity ({unit})", fontsize=11)

default_matplotlib_save(fig, IMAGE_FOLDER / f"report_evhub_striplot.png")

#%% stripplot with hue clusters

db = pd.read_pickle(RESOURCE_FOLDER / "evhub_2210_v2_clustered.pkl")
db.rename({"clusters_from_gridcap": "clusters"}, axis=1, inplace=True)
db['clusters'] = db['clusters'].apply(lambda x: int(x[0]))
fig, axi = plt.subplots(4, 1, figsize=(6, 5), gridspec_kw={"height_ratios": [*[5]*3,3]})
plt.tight_layout(pad=0.3)
rc = {
    "font.family": "Open Sans",
    "font.size": 10,
    "legend.fontsize": 8,
}
plt.rcParams.update(rc)
plt.subplots_adjust(hspace=0.1)
for ax in axi.flat:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


for i, (tech, col) in enumerate(tech_dict.items()):
    if tech == "battery":
        unit = "MWh"
    else:
        unit = "MW"
    ax=axi[i]
    sns.stripplot(
        x=col,
        y="grid_capacity",
        data=db,
        hue="clusters",
        ax=ax,
        orient="h",
        size=2.3,
        alpha=0.7,
        jitter=0.5,
        palette="mako",
    )

    ax.get_legend().remove()
    ax.set_ylabel("grid capacity (MW)", fontsize=9)
    ax.set_xlabel(f"{tech} deployed capacity ({unit})")

axi[-1].axis("off")
axi[-1].legend(
    handles=[Patch(facecolor=c, edgecolor=c, label=f"cluster {i+1}") for i, c in enumerate(sns.color_palette("mako", n_colors=5))],
    frameon=False,
    ncol=5,
    loc="upper center",
    title="clusters",
)

default_matplotlib_save(
    fig, IMAGE_FOLDER / f"report_evhub_striplot_clusters.png",
)


# %%
if input("Crop the images in this folder? [y/n]") == "y":
    from LESO.plotting import crop_transparency_top_bottom
    crop_transparency_top_bottom(
        folder_to_crop=IMAGE_FOLDER,
        file_ext_to_crop="png",
        override_original=True
    ) 