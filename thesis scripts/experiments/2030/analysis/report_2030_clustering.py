# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.spatial.distance import squareform
from sklearn.cluster import AgglomerativeClustering
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

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
COLLECTION = "gld2030"
RUN_ID = "2310_v2"
palette = "mako"

#%% load in results
db = get_data_from_db(collection=COLLECTION, run_id=RUN_ID, force_refresh=False)

#%% CLUSTERING

targets = [
    "no_target",
    "current_projection_excl_export",
    "fixed_target_60",
    "fixed_target_80",
    "fixed_target_100"
]
for target in targets:

    df = db.query(f"target_RE_strategy == {target}")

    # subset-df
    sdf = df[[total_bat_col, pv_col, wind_col]].copy()
    sdf.columns = ["battery", "pv", "wind"]
    sarr = sdf.values

    scaled = StandardScaler().fit_transform(sarr)

    cluster_labels = AgglomerativeClustering(
        affinity="cosine",
        linkage="complete",
        distance_threshold=1,
        compute_full_tree=True,
        n_clusters=None,
    ).fit_predict(scaled)

    labels, counts = np.unique(cluster_labels, return_counts=True)
    label_map = {key: value for key, value in zip(labels, counts)}
    label_with_count = lambda x: f"{x} (n={label_map[x]})"
    cluster_labels_with_count = [label_with_count(x) for x in cluster_labels]
    sdf["cluster"] = cluster_labels_with_count

    embedded_space = TSNE(
        n_components=2,
        learning_rate=12,
        metric="cosine",
        square_distances=True,
        perplexity=12,
    ).fit_transform(scaled)

    tsne_x, tsne_y = embedded_space[:, 0], embedded_space[:, 1]

    fig, ax = plt.subplots(figsize=(3, 2))
    fig, ax = default_matplotlib_style(fig, ax)
    sns.scatterplot(
        x=tsne_x,
        y=tsne_y,
        hue=cluster_labels,
        ax=ax,
        palette=palette,
        alpha=0.3,
    )
    default_matplotlib_save(
        fig, IMAGE_FOLDER / f"analysis_{COLLECTION}_clustering_t-SNE_{target}.png"
    )

    fig, ax = plt.subplots(figsize=(3, 2))
    fig, ax = default_matplotlib_style(fig, ax)
    sns.scatterplot(
        data=sdf,
        x="pv",
        y="wind",
        hue="cluster",
        sizes=(100, 250),
        ax=ax,
        palette=palette,
        alpha=0.3,
    )
    ax.set_ylabel("deployed wind capacity (MW)")
    ax.set_xlabel("deployed PV capacity (MW)")
    default_matplotlib_save(
        fig,
        IMAGE_FOLDER / f"analysis_{COLLECTION}_clustering_pvwind_capacities_{target}.png",
    )

    db.loc[df.index, "clusters_from_gridcap"] = cluster_labels_with_count


#%% pairplots

font_size = FONTSIZE
decrease_legend = False
pairplot_cols = [
    "pv_cost_factor",
    "wind_cost_factor",
    "battery_cost_factor",
    "clusters_from_gridcap",
]
for target in targets:
    df = db.query(f"targetacity == {target}").copy()
    # subset-df
    sdf = df[pairplot_cols].copy()
    sdf.columns = [
        "battery cost factor",
        "pv cost factor",
        "wind cost factor",
        "clusters",
    ]

    hue_order = {}
    for name in sdf.clusters.unique():
        for x in range(len(sdf.clusters.unique())):
            if f"{x} (" in name:
                value = x
        hue_order.update({name: value})

    plt.tight_layout(pad=PAD)

    rc = {
        "font.family": "Open Sans",
        "font.size": font_size,
        "legend.fontsize": font_size,
    }
    g = sns.pairplot(
        sdf, hue="clusters", hue_order=hue_order, palette=palette, plot_kws={"size": 10}
    )

    g._legend_data.pop("10")

    handles = g._legend_data.values()
    labels = g._legend_data.keys()
    g._legend.remove()

    g.fig.legend(
        bbox_to_anchor=(0.5, -0.1),
        handles=handles,
        labels=labels,
        loc="lower center",
        frameon=True,
        title="clusters",
        ncol=5,
    )
    plt.subplots_adjust(bottom=0.1)
    g.fig.set_size_inches(6, 5)
    plt.savefig(
        IMAGE_FOLDER / f"report_{COLLECTION}_clustering_pairplot_{target}_grid.png",
        dpi=300,
        bbox_inches="tight",
    )


#%%

db.to_pickle(RESOURCE_FOLDER / "{COLLECTION}_2210_v2_clustered.pkl")


#%%
cols_of_interest = [
    total_bat_col,
    pv_col,
    wind_col,
    "relative_curtailment",
    "pv_cost_factor",
    "wind_cost_factor",
    "battery_cost_factor",
    "total_generation",
    "objective_result",
]
translated_cols = [
    "battery energy",
    "PV power",
    "wind power",
    "curtailment",
    "PV cost",
    "wind cost",
    "battery cost",
    "total generation",
    "profitability",
]

# plot
fig, axi = plt.subplots(2, 2)
fig.set_size_inches(6, 6)
rc = {
    "font.family": "Open Sans",
    "font.size": 8,
}
axi = axi.flatten()
for ax in axi:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

plt.rcParams.update(rc)
cbar_ax = fig.add_axes([0.9, 0.85, 0.01, 0.1])
first = True
for i, target in enumerate(targets):

    # select the grid capacity
    df = db.query(f"targetacity == {target}").copy()
    df["objective_result"] = -df["objective_result"]

    # subset-df
    sdf = df[cols_of_interest].copy()
    sdf.columns = translated_cols

    # calculate corr matrix
    corr_mat = sdf.corr(method="pearson")
    mask = np.zeros_like(corr_mat)
    mask[np.triu_indices_from(mask)] = True

    figgy = sns.heatmap(
        corr_mat,
        ax=axi[i],
        mask=mask,
        square=True,
        annot=True,
        fmt=".1f",
        annot_kws={"fontsize": 6},
        vmin=-1,
        vmax=1,
        cmap="mako",
        cbar=first,
        cbar_ax=cbar_ax,
    )
    first = False
    axi[i].text(
        0.45,
        1,
        f"{target} MW grid",
        horizontalalignment="center",
        verticalalignment="center",
        transform=axi[i].transAxes,
        fontdict={"fontsize": 10,}
    )


default_matplotlib_save(
    fig, IMAGE_FOLDER / f"report_{COLLECTION}_correlation_matrix_all_grid.png"
)

#%%
dbc = db.copy()
dbc["objective_result"] = -dbc["objective_result"]

# subset-df
sdb = dbc[cols_of_interest].copy()
sdb.columns = translated_cols

# calculate corr matrix
corr_mat = sdb.corr(method="pearson")
mask = np.zeros_like(corr_mat)
mask[np.triu_indices_from(mask)] = True

# plot
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
sns.heatmap(corr_mat, ax=ax, mask=mask, square=True, annot=True, fmt=".1f")

# %%
if input("Crop the images in this folder? [y/n]") == "y":
    from LESO.plotting import crop_transparency_top_bottom
    crop_transparency_top_bottom(
        folder_to_crop=IMAGE_FOLDER,
        file_ext_to_crop="png",
        override_original=True
    ) 
