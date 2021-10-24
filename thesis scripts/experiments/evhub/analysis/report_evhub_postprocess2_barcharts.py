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
    bivar_tech_dict
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
db = get_data_from_db(
    collection=COLLECTION,
    run_id=RUN_ID,
    force_refresh=False
)


#%% enter the loop:
grid_capacities = {
    0: (33, 31),
    0.5: (24, 22),
    1: (11.3, 11),
    1.5: (6.5, 6),
}

ref_df = pd.DataFrame()
ref_idx = {}
for grid_cap, (upper_limit, lower_limit) in grid_capacities.items():
    df = db.query(f"grid_capacity == {grid_cap}").copy(deep=True)

    cols_of_interest = [pv_col, wind_col, total_bat_col]
    df_barplot = pd.DataFrame(index=cols_of_interest)

    ## 3 configs
    
    # med battery deployment
    subset = df[df[total_bat_col]< upper_limit]
    subset = subset[subset[total_bat_col]> lower_limit]
    subset_idx = subset[total_bat_col].argmax()
    df_barplot["reference"] = subset.loc[subset.index[subset_idx],cols_of_interest].copy(deep=True)
    ref_idx.update({grid_cap: subset.index[subset_idx]})
    
    if grid_cap == 1.5: # for 1.5 grid, the 
        ref_idx.update({grid_cap: subset.index[subset_idx]})
    
    # minimum PV+wind deployment
    idx = df[pv_col].argmax()
    df_barplot["max PV"] = df.loc[df.index[idx],cols_of_interest].copy(deep=True)

    # max PV+wind deployment
    idx = df[wind_col].argmax()
    df_barplot["max wind"] = df.loc[df.index[idx],cols_of_interest].copy(deep=True)
        

    df_barplot.index = ['PV', 'wind', 'battery']
    df_barplot = df_barplot.T
    df_barplot["grid"] = grid_cap

    #%% PV Deployment vs absolut cost scatter
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
    fig.set_size_inches(4,3)
    color={"PV": "#edc645", "wind": "steelblue", 'battery': "darkseagreen", "grid": "darkgrey"}
    df_barplot.plot.bar(stacked=True, ax=ax, color=color)

    ax.set_ylabel("total capacity (MW)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation = 0, fontsize=9)
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
            labels = [round(v.get_height(),1) if v.get_height() > 0 else '' for v in c]
        else:
            labels = [(int(v.get_height()) if v.get_height() > 1 else round(v.get_height(),1)) if v.get_height() > 0.1 else '' for v in c]
        
        # remove the labels parameter if it's not needed for customized labels
        ax.bar_label(c, labels=labels, label_type='center', color="#404040")

    default_matplotlib_save(fig, IMAGE_FOLDER / f"report_evhub_grid-{grid_cap}_configurations.png")

    ref_df[f'{grid_cap} MW'] = df_barplot.T['reference']

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
fig.set_size_inches(4,3)
color={"PV": "#edc645", "wind": "steelblue", 'battery': "darkseagreen", "grid": "darkgrey"}
ref_df.T.plot.bar(stacked=True, ax=ax, color=color)

ax.set_ylabel("total capacity (MW)")
ax.set_xlabel("grid capacity")
ax.set_xticklabels(ax.get_xticklabels(), rotation = 0, fontsize=9)
ax.legend(
    bbox_to_anchor=(1.02, 0.5),
    loc=6,
    borderaxespad=0.0,
    frameon=False,
)


for c in ax.containers:

    # Optional: if the segment is small or 0, customize the labels
    if c.get_label() == "grid":
        labels = [round(v.get_height(),1) if v.get_height() > 0 else '' for v in c]
    else:
        labels = [int(v.get_height()) if v.get_height() > 0.5 else '' for v in c]
    
    # remove the labels parameter if it's not needed for customized labels
    ax.bar_label(c, labels=labels, label_type='center', color="#404040")

default_matplotlib_save(fig, IMAGE_FOLDER / f"report_evhub_grid_configurations_compare.png")

