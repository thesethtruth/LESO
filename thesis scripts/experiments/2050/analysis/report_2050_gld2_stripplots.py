# report_2030_gld1_heatmaps.py
# %%
from numpy.core.fromnumeric import size
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from seaborn import palettes
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.collections import PolyCollection

from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from LESO.plotting import PAD, FONTSIZE
from util_2050_postprocess_tools import (
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
COLLECTION = "gld2050"
RUN_ID = "2710_v2"
palette = sns.color_palette("mako", n_colors=4)

## maps
col_map = {
    pv_col: "PV",
    wind_col: "wind",
    total_bat_col: "battery",
    total_h2_col: "hydrogen",
}
features = list(col_map.values())
scenarios = {
    "Gelderland_2050_regional": {
        "title": "Regional",
        "clusters": 4,  # maybe 5
        "sort": 1,
    },
    "Gelderland_2050_national": {
        "title": "National",
        "clusters": 4,  # four for sure
        "sort": 2,
    },
    "Gelderland_2050_european": {
        "title": "European",
        "clusters": 4,  # maybe 5
        "sort": 3,
    },
    "Gelderland_2050_international": {
        "title": "International",
        "clusters": 4,  # four for sure
        "sort": 4,
    },
}
cluster_col = "clusters_predef_num_clusters"
scenario_col = "scenario"

#%% fetch and process data
db = pd.read_pickle(RESOURCE_FOLDER / f"{COLLECTION}_2210_v2_clustered.pkl")

## rename columns
db.rename(col_map, inplace=True, axis=1)
db["sort"] = db.scenario.apply(lambda x: scenarios[x]["sort"])
db.sort_values(["sort", cluster_col], inplace=True)
db["scenario"] = db.scenario.apply(lambda x: scenarios[x]["title"])

df = db[[*features, cluster_col, scenario_col]].copy()
df[features] = df[features] / 1000

palette_d = []
for attribute in scenarios.values():
    pal = palette[: attribute["clusters"]]
    attribute.update({"palette": pal})
    palette_d.extend(pal)
#%% =================================================================================================
##                      Stripplot


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

    sns.swarmplot(
        x=feature,
        y=scenario_col,
        data=df,
        hue=cluster_col,
        ax=ax,
        orient="h",
        size=2,
        alpha=1,
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
    IMAGE_FOLDER / f"report_{COLLECTION}_swarmplot_clusters_all_scenarios.png",
)


#%%

for fn_scenario, attribute in scenarios.items():
    scenario = attribute["title"]
    sdf = df.query(f"scenario == '{scenario}'")
    fig, axi = plt.subplots(
        5, 1, figsize=(6, 5), gridspec_kw={"height_ratios": [*[5] * 4, 1]}
    )
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

        sns.stripplot(
            x=feature,
            y=cluster_col,
            data=sdf,
            hue=cluster_col,
            ax=ax,
            orient="h",
            size=2,
            alpha=1,
            jitter=0.45,
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
    axi[-1].axis("off")
    axi[-1].legend(
        handles=[
            Patch(facecolor=c, edgecolor=c, label=i)
            for i, c in enumerate(palette[: attribute["clusters"]])
        ],
        frameon=True,
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        loc="upper center",
        title="clusters",
    )

    default_matplotlib_save(
        fig,
        IMAGE_FOLDER / f"report_{COLLECTION}_striplot_clusters_{fn_scenario}.png",
    )
#%% SWARM PLOT?

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

    sns.stripplot(
        x=feature,
        y=scenario_col,
        data=df,
        hue=cluster_col,
        ax=ax,
        orient="h",
        size=2,
        alpha=1,
        jitter=0.45,
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
    IMAGE_FOLDER / f"report_{COLLECTION}_striplot_clusters_all_scenarios.png",
)

#%% VIOLIN?

#%%
for feature in features:

    if "battery" in feature or "hydrogen" in feature:
        unit = "GWh"
    else:
        unit = "GW"

    g = sns.FacetGrid(
        df, row="scenario", hue=cluster_col, aspect=15, height=1, palette=palette
    )
    rc = {
        "font.family": "Open Sans",
        "font.size": 10,
    }

    plt.rcParams.update(rc)
    # for cluster in sdf[cluster_col].unique():
    g.map(sns.kdeplot, feature, clip_on=False, color="w", lw=4, bw_adjust=0.5)
    g.map(
        sns.kdeplot, feature, bw_adjust=0.5, clip_on=False, fill=True, alpha=0.7, linewidth=1.5
    )

    g.despine(bottom=False, left=True)
    scenarios_ = df.scenario.unique()
    for i, ax in enumerate(g.axes.flat):
        lvl = -i * 10
        artists = ax.get_children()
        
        if ax is not g.axes.flat[-1]:
            ax.spines["bottom"].set_visible(False)
            ax.tick_params(
                axis="both",
                which="both",
                left=False,
                bottom=False,
                labelleft=True,
            )
        else:
            ax.set_xlabel(f"{feature} deployed capacity ({unit})")

        ax.set_ylabel(scenarios_[i], rotation=0, ha='right', va="top")
        

        for artist in artists:

            if isinstance(artist, Line2D):
                artist.set_zorder(lvl - 2 )
            if isinstance(artist, PolyCollection):
                artist.set_zorder(lvl)

    # Set the subplots to overlap
    g.fig.subplots_adjust(hspace=-0.4)


    # Remove axes details that don't play well with overlap
    g.set_titles("")
    g.set(yticks=[])

    g.fig.set_size_inches(6, 2)
    plt.tight_layout(pad=PAD)

    plt.savefig(
        IMAGE_FOLDER / f"report_{COLLECTION}_facetgrid_clusters_all_scenarios_{feature}.png", dpi=300
    )
# %%
if input("Crop the images in this folder? [y/n]") == "y":
    from LESO.plotting import crop_transparency_top_bottom

    crop_transparency_top_bottom(
        folder_to_crop=IMAGE_FOLDER, file_ext_to_crop="png", override_original=True
    )
