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
palette = "mako"

#%% load in results
db = pd.read_pickle(RESOURCE_FOLDER / "evhub_2210_v2_clustered.pkl")

def normalize_stack(df):
    result = df.copy()
    for idx in df.index:
        sum = df.T[idx].sum()
        for col in df.columns:
            result.loc[idx, col] = df.loc[idx, col] / sum
        
    result = result*100
    return result


#%% SELECTING THE DATA
normalize = True
grid_capacities = [0, 0.5, 1, 1.5]
ref_df = pd.DataFrame()
design_cols = [pv_col, wind_col, total_bat_col, "grid_capacity"]

for grid_cap in grid_capacities:
    df = db.query(f"grid_capacity == {grid_cap}").copy()
    df_barplot = df[design_cols].groupby(df.clusters_from_gridcap).median()
    df_barplot.columns = ['PV', 'wind', 'battery', 'grid']

    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
    fig.set_size_inches(4, 3)
    color = {
        "PV": "#edc645",
        "wind": "steelblue",
        "battery": "darkseagreen",
        "grid": "darkgrey",
    }
    if normalize:
        df_barplot = normalize_stack(df_barplot)
        file_name = f"report_evhub_cluster_grid-{grid_cap}_configurations_normed.png"
        unit = "%"
    else:
        file_name = f"report_evhub_cluster_grid-{grid_cap}_configurations.png"
        unit= "MW(h)"
    df_barplot.plot.bar(stacked=True, ax=ax, color=color)

    ax.set_ylabel(f"total capacity ({unit})")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=9)
    ax.legend(
        bbox_to_anchor=(1.02, 0.5),
        loc=6,
        borderaxespad=0.0,
        frameon=False,
    )

    for c in ax.containers:
        v = c[0]
        # Optional: if the segment is small or 0, customize the labels
        if c.get_label() == "grid":
            labels = [round(v.get_height(), 1) if v.get_height() > 0 else "" for v in c]
        else:
            labels = [
                (
                    int(v.get_height())
                    if v.get_height() > 1
                    else round(v.get_height(), 1)
                )
                if v.get_height() > 0.1
                else ""
                for v in c
            ]

        # remove the labels parameter if it's not needed for customized labels
        ax.bar_label(c, labels=labels, label_type="center", color="#404040")

    default_matplotlib_save(
        fig, IMAGE_FOLDER / file_name
    )
    
    highest_cluster_count = 0
    for i in df_barplot.index:
        current_count = float(i[5:-1])
        if current_count > highest_cluster_count:
            ref_index = i
            highest_cluster_count = current_count


    ref_df[f"{grid_cap} MW"] = df_barplot.T[ref_index]

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
fig.set_size_inches(4, 3)
color = {
    "PV": "#edc645",
    "wind": "steelblue",
    "battery": "darkseagreen",
    "grid": "darkgrey",
}
ref_df.T.plot.bar(stacked=True, ax=ax, color=color)

ax.set_ylabel("total capacity (MW(h))")
ax.set_xlabel("grid capacity")
ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=9)
ax.legend(
    bbox_to_anchor=(1.02, 0.5),
    loc=6,
    borderaxespad=0.0,
    frameon=False,
)


for c in ax.containers:

    # Optional: if the segment is small or 0, customize the labels
    if c.get_label() == "grid":
        labels = [round(v.get_height(), 1) if v.get_height() > 0 else "" for v in c]
    else:
        labels = [int(v.get_height()) if v.get_height() > 0.5 else "" for v in c]

    # remove the labels parameter if it's not needed for customized labels
    ax.bar_label(c, labels=labels, label_type="center", color="#404040")

default_matplotlib_save(
    fig, IMAGE_FOLDER / f"report_evhub_cluster_configurations_compare.png"
)
