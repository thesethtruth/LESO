# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

from LESO.experiments.analysis import (
    load_ema_leso_results,
    open_leso_experiment_file,
)
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% constants
FOLDER = Path(__file__).parent
FIG_FOLDER = FOLDER / "images"
RESULT_FOLDER = FOLDER.parent / "results"

run_id = 210907

#%% load in results
experiments, outcomes, db = load_ema_leso_results(
    run_id=run_id, 
    exp_prefix="evhub",
    results_folder=RESULT_FOLDER)

## needed for more kpis
spec_yield_pv = 1025.307
spec_yield_wind = 2937.6


## pointers
pv_col = "PV South installed capacity"
wind_col = "Nordex N100 2500 installed capacity"
bat_col = "2h battery installed capacity"

## change / add some data
db['pv_cost_absolute'] = db.pv_cost_factor * 1020
db['wind_cost_absolute'] = db.wind_cost_factor * 1350
db['curtailment'] = -db['curtailment']
db['total_generation'] = (db[pv_col] * spec_yield_pv + db[wind_col]*spec_yield_wind)
db['relative_curtailment'] = db['curtailment'] / db['total_generation'] *100
db['total_installed_capacity'] = db[pv_col] + db[wind_col]


def linear_map(value, ):
    min, max = 0.41, 0.70 # @@
    map_min, map_max = 0.42, 0.81 # @@

    frac = (value - min) / (max-min)
    m_value = frac * (map_max-map_min) + map_min

    return m_value

power_ref = 257
storage_ref = 277

db["battery_cost_absolute_2h"] = [
    (bcf * storage_ref *2 + linear_map(bcf)*power_ref)/2
    for bcf in db["battery_cost_factor"].values
]


#%% enter the loop:
grid_capacities = {
    0: 27.5,
    0.5: 15,
    1: 9,
    1.5: 3,
}

ref_df = pd.DataFrame()
ref_idx = {}
for grid_cap, filter_limit in grid_capacities.items():
    df = db.query(f"grid_capacity == {grid_cap}").copy(deep=True)

    cols_of_interest = [pv_col, wind_col, bat_col]
    df_barplot = pd.DataFrame(index=cols_of_interest)

    # 3 configs for 0 grid cap
    # max battery deployment
    idx = df[bat_col].argmax()
    df_barplot["reference"] = df.loc[df.index[idx],cols_of_interest].copy(deep=True)
    ref_idx.update({grid_cap: df.index[idx]})
    # med battery deployment
    subset = df[df[bat_col]< filter_limit]
    subset_idx = subset[bat_col].argmax()
    df_barplot["in-between"] = subset.loc[subset.index[subset_idx],cols_of_interest].copy(deep=True)
    
    if grid_cap == 1.5: # for 1.5 grid, the 
        ref_idx.update({grid_cap: subset.index[subset_idx]})
        # max pv deployment
    idx = df[pv_col].argmax()
    df_barplot["PV oversized"] = df.loc[df.index[idx],cols_of_interest].copy(deep=True)

    if grid_cap == 1.5:
        org_order = df_barplot.columns
        df_barplot.columns = ["in-between","reference", "PV oversized"]
        df_barplot = df_barplot[org_order]
        

    df_barplot.index = ['PV', 'wind', 'li-ion ESS']
    df_barplot = df_barplot.T
    df_barplot["grid"] = grid_cap

    #%% PV Deployment vs absolut cost scatter
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
    fig.set_size_inches(4,3)
    color={"PV": "#edc645", "wind": "steelblue", 'li-ion ESS': "darkseagreen", "grid": "darkgrey"}
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

        # Optional: if the segment is small or 0, customize the labels
        if c.get_label() == "grid":
            labels = [round(v.get_height(),1) if v.get_height() > 0 else '' for v in c]
        else:
            labels = [int(v.get_height()) if v.get_height() > 0.5 else '' for v in c]
        
        # remove the labels parameter if it's not needed for customized labels
        ax.bar_label(c, labels=labels, label_type='center', color="#404040")

    default_matplotlib_save(fig, FIG_FOLDER / f"report_evhub_grid-{grid_cap}_configurations.png")

    ref_df[f'{grid_cap} MW'] = df_barplot.T['reference']

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
fig.set_size_inches(4,3)
color={"PV": "#edc645", "wind": "steelblue", 'li-ion ESS': "darkseagreen", "grid": "darkgrey"}
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

default_matplotlib_save(fig, FIG_FOLDER / f"report_evhub_grid_configurations_compare.png")

