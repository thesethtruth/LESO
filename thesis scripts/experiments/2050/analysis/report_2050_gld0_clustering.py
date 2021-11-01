# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

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
IMAGE_FOLDER.mkdir(exist_ok=True)
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
COLLECTION = "gld2050"
RUN_ID = "2710_v2"
palette = sns.color_palette("mako", n_colors=4)
cmap = sns.diverging_palette(190, 130, l=50, s=90, as_cmap=True)
pair_plot_fontsize = 8
only_predefined = True

## maps
scenarios = {
    "Gelderland_2050_regional": {
        "title": "Regional", 
        "clusters": 4, # maybe 5
        "sort": 1
    },
    "Gelderland_2050_national": {
        "title": "National", 
        "clusters": 4, # four for sure
        "sort": 2
    },
    "Gelderland_2050_european": {
        "title": "European", 
        "clusters": 4, # maybe 5
        "sort": 3
    },
    "Gelderland_2050_international": {
        "title": "International",
        "clusters": 4, # four for sure
        "sort": 4,
    },
}

col_map = {
    pv_col: "PV",
    wind_col: "wind",
    total_bat_col: "battery",
    total_h2_col: "hydrogen",
}

pairplot_col_map = {
    "pv_cost_factor": "pv cost factor",
    "wind_cost_factor": "wind cost factor",
    "battery_cost_factor": "battery cost factor",
    "hydrogen_cost_factor": "hydrogen cost factor",
}

features = list(col_map.values())

#%% load in results
db = get_data_from_db(collection=COLLECTION, run_id=RUN_ID, force_refresh=False)

## rename columns
db.rename(col_map, inplace=True, axis=1)
db.rename(pairplot_col_map, inplace=True, axis=1)


#%% =================================================================================================
##                      CLUSTERING
clusters = []
for scenario, settings in scenarios.items():

    df = db.query(f"scenario == '{scenario}'")

    # subset-df
    sdf = df[features].copy()
    sarr = sdf.values

    scaled = StandardScaler().fit_transform(sarr)

    for distance_based in [True, False]:

        label = "dis_threshold" if distance_based else "predef_num_clusters"

        cluster_labels = AgglomerativeClustering(
            affinity="cosine",
            linkage="complete",
            distance_threshold=1 if distance_based else None,
            compute_full_tree=True,
            n_clusters=settings["clusters"] if not distance_based else None,
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
            palette="mako",
            alpha=0.3,
        )
        default_matplotlib_save(
            fig,
            IMAGE_FOLDER
            / f"analysis_{COLLECTION}_clustering_t-SNE_{scenario}_{label}.png",
        )
        cl = f"clusters_{label}"
        clusters.append(cl)
        db.loc[df.index, cl] = cluster_labels_with_count
clusters = set(clusters)
db.to_pickle(RESOURCE_FOLDER / "{COLLECTION}_2210_v2_clustered.pkl")

#%% =================================================================================================
##                      PAIRPLOTS

for scenario, settings in scenarios.items():

    df = db.query(f"scenario == '{scenario}'").copy()
    for cl in clusters:
        if cl == "clusters_dis_threshold" and only_predefined:
            pass
        else:
            # subset-df
            sdf = df[[*pairplot_col_map.values(), cl]].copy()
            sdf.sort_values(cl, inplace=True)
            ncl = len(sdf[cl].unique())
            if cl == "clusters_dis_threshold":
                pal = "mako"
            else:
                pal = palette[:ncl]

            plt.tight_layout(pad=PAD)

            rc = {
                "font.family": "Open Sans",
                "font.size": pair_plot_fontsize,
            }
            plt.rcParams.update(rc)
            g = sns.pairplot(sdf, hue=cl, palette=pal, plot_kws={"size": 10})

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
                IMAGE_FOLDER / f"report_{COLLECTION}_{cl}_pairplot_{scenario}.png",
                dpi=300,
                bbox_inches="tight",
            )
