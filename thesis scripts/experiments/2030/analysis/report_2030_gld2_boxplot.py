# report_2030_gld2_heatmaps.py
# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from seaborn import palettes
from matplotlib.patches import Patch

from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from LESO.plotting import PAD, FONTSIZE
from util_2030_postprocess_tools import (
    get_data_from_db,
    gcloud_read_experiment,
    pv_col,
    wind_col,
    bat2_col,
    bat6_col,
    bat10_col,
    total_bat_col,
    total_h2_col,
    batcols,
    bivar_tech_dict,
    grid_col,
)

#%% paths
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
COLLECTION = "gld2030"
RUN_ID = "2310_v2"
palette = sns.color_palette("mako", n_colors=4)

## maps
col_map = {
    pv_col: "PV",
    wind_col: "wind",
    total_bat_col: "battery",
    total_h2_col: "hydrogen",
}
features = list(col_map.values())
targets = {
    "no_target": {"title": "No target", "sort": 1, "clusters": 2},
    "fixed_target_60": {"title": "60% target", "sort": 2, "clusters": 3},
    "fixed_target_80": {"title": "80% target", "sort": 3, "clusters": 4},
    "fixed_target_100": {"title": "100% target", "sort": 4, "clusters": 4},
}
cluster_col = "clusters_predef_num_clusters"
target_col = "target_RE_strategy"

#%% fetch and process data
db = pd.read_pickle(RESOURCE_FOLDER / "{COLLECTION}_2210_v2_clustered.pkl")

## rename columns
db.rename(col_map, inplace=True, axis=1)
db["sort"] = db.target_RE_strategy.apply(lambda x: targets[x]["sort"])
db.sort_values(["sort", cluster_col], inplace=True)
db["target_RE_strategy"] = db.target_RE_strategy.apply(lambda x: targets[x]["title"])

df = db[[*features, cluster_col, target_col]].copy()
df[features] = df[features] / 1000

palette_d = []
for attribute in targets.values():
    pal = palette[: attribute["clusters"]]
    attribute.update({"palette": pal})
    palette_d.extend(pal)
#%% =================================================================================================
##                      Boxplot


fig, axi = plt.subplots(4, 1, figsize=(6, 8))
plt.tight_layout(pad=PAD)
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

axs = axi.flat
for i, (feature) in enumerate(features):
    ax = axs[i]

    if "battery" in feature or "hydrogen" in feature:
        unit = "GWh"
    else:
        unit = "GW"

    sns.boxplot(
        x=feature,
        y=target_col,
        data=df,
        hue=cluster_col,
        ax=ax,
        orient="h",
        palette=palette_d,
    )

    ax.get_legend().remove()
    ax.set_ylabel("")
    ax.set_xlabel(f"{feature} deployed capacity ({unit})")


axi[0].legend(
    handles=[Patch(facecolor=c, edgecolor=c, label=i) for i, c in enumerate(palette)],
    frameon=False,
    ncol=1,
    loc="upper right",
    title="clusters",
)

default_matplotlib_save(
    fig,
    IMAGE_FOLDER / f"report_{COLLECTION}_boxplot_clusters_all_targets.png",
)


#%%

for fn_target, attribute in targets.items():
    target = attribute["title"]
    sdf = df.query(f"target_RE_strategy == '{target}'")
    fig, axi = plt.subplots(5, 1, figsize=(6, 8), gridspec_kw={'height_ratios': [*[5]*4,1]})
    plt.tight_layout(pad=PAD)
    plt.subplots_adjust(bottom=0.8)
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
        ax.spines["left"].set_visible(False)

    axs = axi.flat

    for i, (feature) in enumerate(features):

        ax = axs[i]

        if "battery" in feature or "hydrogen" in feature:
            unit = "GWh"
        else:
            unit = "GW"

        sns.boxplot(
            x=feature,
            y=cluster_col,
            data=sdf,
            hue=cluster_col,
            ax=ax,
            orient="h",
            palette=attribute["palette"],
        )

        ax.get_legend().remove()
        ax.set_ylabel("")
        ax.set_yticklabels([])
        ax.set_xlabel(f"{feature} deployed capacity ({unit})")
        ax.set_xlim([-0.3, sdf.max()[feature] if sdf.max()[feature] > 15 else 15])

        ax.tick_params(
            axis="both",
            which="both",
            left=False,
            labelleft=False,
        )
    axi[-1].axis('off')
    axi[-1].legend(
        handles=[
            Patch(facecolor=c, edgecolor=c, label=i) 
            for i, c in enumerate(
                palette[:attribute["clusters"]]
                )
        ],
        frameon=True,
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        loc="upper center",
        title="clusters",
    )
    

    default_matplotlib_save(
        fig,
        IMAGE_FOLDER / f"report_{COLLECTION}_boxplot_clusters_{fn_target}.png",
    )


# %%
if input("Crop the images in this folder? [y/n]") == "y":
    from LESO.plotting import crop_transparency_top_bottom

    crop_transparency_top_bottom(
        folder_to_crop=IMAGE_FOLDER, file_ext_to_crop="png", override_original=True
    )
