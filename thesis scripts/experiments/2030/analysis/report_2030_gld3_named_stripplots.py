# report_2030_gld1_heatmaps.py
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
    cluster_map,
)

#%% paths
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
COLLECTION = "gld2030"
palette = sns.color_palette("mako", n_colors=4)

## maps
col_map = {
    pv_col: "PV",
    wind_col: "wind",
    total_bat_col: "battery",
    total_h2_col: "hydrogen",
}
features = ['PV', 'wind', 'battery', 'hydrogen']
targets = {
    "no_target": {"title": "No target", "sort": 1, "clusters": 2},
    "fixed_target_60": {"title": "60% target", "sort": 2, "clusters": 3},
    "fixed_target_80": {"title": "80% target", "sort": 3, "clusters": 4},
    "fixed_target_100": {"title": "100% target", "sort": 4, "clusters": 4},
}
target_col = "target_RE_strategy"
cluster_col = "clusters_predef_num_clusters"
generic_cluster_order = ['max. PV', 'PV&hydrogen', 'wind&hydrogen', 'max. wind']
#%% fetch and process data
db = pd.read_pickle(RESOURCE_FOLDER / f"{COLLECTION}_2210_v2_clustered.pkl")

## rename clusters and implement sorting
db["sort"] = db.target_RE_strategy.apply(lambda x: targets[x]["sort"])

for target, gdf in db.groupby("target_RE_strategy"):
    
    target_map = cluster_map[target]
    def cluster_order(x):
        cluster_num = int(x[0])
        return target_map[cluster_num]['order']
    db.loc[gdf.index,'cluster_sort'] = gdf[cluster_col].apply(cluster_order)

    predef_clusters = gdf[cluster_col].unique()
    temp_lst = []
    for pclus in predef_clusters:
        cluster_num = int(pclus[0])
        count = pclus.split(" ")[1]

        temp_lst.append(
            (target_map[cluster_num]["order"], target_map[cluster_num]["name"]+" "+count),
        )
    temp_lst = [y for _, y in sorted(temp_lst)]

    target_map.update({"cluster_list": temp_lst})

t_cluster_map = {}
for key in cluster_map.keys():
    t_cluster_map.update({
        targets[key]['title']:cluster_map[key]
    })
cluster_map = t_cluster_map
db["target_RE_strategy"] = db.target_RE_strategy.apply(lambda x: targets[x]["title"])
db.sort_values(["sort", "cluster_sort"], inplace=True)
df = db[[*features, "cluster_sort", target_col]].copy()
df[features] = df[features] / 1000



#%% =================================================================================================
##                      Stripplot


fig, axi = plt.subplots(5, 1, figsize=(6, 8), gridspec_kw={"height_ratios": [*[5]*4,4]})
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
        y=target_col,
        data=df,
        hue="cluster_sort",
        ax=ax,
        orient="h",
        size=2,
        alpha=1,
        jitter=0.45,
        palette=palette,
    )

    ax.get_legend().remove()
    ax.set_ylabel("")
    ax.set_xlabel(f"{feature} deployed capacity ({unit})")

y=1
pos = [tuple([-0.1+x*0.32,y]) for x in range(4)]
axi[-1].axis("off")
legends =[]
for i, target in enumerate(cluster_map.keys()):
    target_clusters = cluster_map[target]["cluster_list"]
    
    legends.append(plt.legend(
        handles=[Patch(facecolor=c, edgecolor=c, label=f"{i+1}: {l}") for i, (l, c) in enumerate(zip(target_clusters, palette))],
        frameon=False,
        ncol=1,
        bbox_to_anchor=pos[i],
        loc="upper center",
        title=f"{target}",
    ))

for leg in legends[:3]:
    axi[-1].add_artist(leg)


default_matplotlib_save(
    fig,
    IMAGE_FOLDER / f"report_{COLLECTION}_striplot_clusters_all_targets.png",
)


#%%

for fn_target, attribute in targets.items():
    target = attribute["title"]
    sdf = df.query(f"target_RE_strategy == '{target}'")
    fig, axi = plt.subplots(5, 1, figsize=(6, 5), gridspec_kw={'height_ratios': [*[5]*4,1]})
    plt.tight_layout(pad=PAD)
    plt.subplots_adjust(bottom=0.1)
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
            y="cluster_sort",
            data=sdf,
            ax=ax,
            orient="h",
            size=2,
            alpha=1,
            jitter=0.45,
            palette=palette,
        )

        # ax.get_legend().remove()
        ax.set_ylabel("")
        ax.set_yticklabels([])
        ax.set_xlabel(f"{feature} deployed capacity ({unit})")
        ax.set_xlim([-0.3, sdf.max()[feature] if sdf.max()[feature] > 5 else 5])

        ax.tick_params(
            axis="both",
            which="both",
            left=False,
            labelleft=False,
        )
    axi[-1].axis('off')
    axi[-1].legend(
        handles=[
            Patch(facecolor=c, edgecolor=c, label=l) 
            for i, (l, c) in enumerate(zip(cluster_map[target]['cluster_list'], palette)
                )
        ],
        frameon=True,
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        loc="upper center",
        title="clusters",
    )
    
    plt.tight_layout(pad=PAD)
    default_matplotlib_save(
        fig,
        IMAGE_FOLDER / f"report_{COLLECTION}_striplot_clusters_{fn_target}.png",
    )


#%% =================================================================================================
##                      PAIRPLOTS

pairplot_col_map = {
    "pv_cost_factor": "pv cost factor",
    "wind_cost_factor": "wind cost factor",
    "battery_cost_factor": "battery cost factor",
    "hydrogen_cost_factor": "hydrogen cost factor",
}
db.rename(pairplot_col_map, inplace=True, axis=1)

for fn_target, attribute in targets.items():
    target = attribute["title"]
    sdf = db.query(f"target_RE_strategy == '{target}'")
    
    sdf = sdf[[*pairplot_col_map.values(), 'cluster_sort']].copy()
    sdf.sort_values("cluster_sort", inplace=True)
    ncl = len(sdf["cluster_sort"].unique())
    pal = palette[:ncl]
    plt.tight_layout(pad=PAD)

    rc = {
        "font.family": "Open Sans",
        "font.size": 8,
    }
    plt.rcParams.update(rc)
    g = sns.pairplot(
        sdf, hue="cluster_sort", palette=pal, plot_kws={"size": 10}
    )

    g._legend_data.pop("10")

    handles = g._legend_data.values()
    labels = g._legend_data.keys()
    g._legend.remove()

    g.fig.legend(
        handles=[
            Patch(facecolor=c, edgecolor=c, label=l) 
            for i, (l, c) in enumerate(zip(cluster_map[target]['cluster_list'], palette)
                )
        ],
        frameon=True,
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        loc="upper center",
        title="clusters",
    )
    plt.subplots_adjust(bottom=0.1)
    g.fig.set_size_inches(6, 5)

    plt.savefig(
        IMAGE_FOLDER / f"report_{COLLECTION}_pairplot_{fn_target}.png",
        dpi=300,
        bbox_inches="tight",
    )


# %%
if input("Crop the images in this folder? [y/n]") == "y":
    from LESO.plotting import crop_transparency_top_bottom

    crop_transparency_top_bottom(
        folder_to_crop=IMAGE_FOLDER, file_ext_to_crop="png", override_original=True
    )
