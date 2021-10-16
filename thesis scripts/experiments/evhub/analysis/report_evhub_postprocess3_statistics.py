# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from seaborn.miscplot import palplot

from LESO.experiments.analysis import (
    load_ema_leso_results,
    open_leso_experiment_file,
)
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% constants
FOLDER = Path(__file__).parent
FIG_FOLDER = FOLDER / "images"
RESULT_FOLDER = FOLDER.parent / "results"
LEFT_MARGIN = 0.15

run_id = 210907

#%% load in results
experiments, outcomes, db = load_ema_leso_results(
    run_id=run_id, exp_prefix="evhub", results_folder=RESULT_FOLDER
)

## note that for 21 cases the optimizer did not exit sucessfully. No clue on how to deal with this. --> ignore it is

## pointers
pv_col = "PV South installed capacity"
wind_col = "Nordex N100 2500 installed capacity"
bat_col = "2h battery installed capacity"
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

# grid_cap2str = lambda x : f"{x} MW"
# db["grid_capacity"] = db["grid_capacity"].apply(grid_cap2str)

#%% start the plots

tech_dict = {"PV": pv_col, "wind": wind_col, "battery": bat_col}

for tech, col in tech_dict.items():
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
    fig.set_size_inches(6,1.5)
    
    sns.stripplot(x=col, y="grid_capacity", data=db, ax=ax, orient='h', size=2, alpha=.3, jitter=.5, edgecolor="black", palette="dark:#69d_r")

    ax.set_ylabel("grid capacity (MW)")
    ax.set_xlabel(f"{tech} deployed capacity (MW)")

    default_matplotlib_save(fig, FIG_FOLDER / f"report_evhub_striplot_{tech}.png")








# %%
