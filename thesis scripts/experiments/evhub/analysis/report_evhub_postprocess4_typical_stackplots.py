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

#%%

ref_idx = {0: 305, 0.5: 27, 1: 205, 1.5: 577}
ref_filenames = {}
for cap, idx in ref_idx.items():
    ref_filenames.update({
        cap: db['filename_export'].iat[idx]
    })
    
# %%
exp = open_leso_experiment_file(RESULT_FOLDER / "evhub_exp_227895.json")
# %%
dates = pd.date_range(
    "01/01/2030",
    freq="h",
    periods=8760,
)
loads = pd.DataFrame(index=dates)
sources = pd.DataFrame(index=dates)

components = exp.components
for ckey in exp.components.keys():

    source = components[ckey].state['power [+]']
    if sum(source) > 1:
        sources[ckey] = source

    load = components[ckey].state['power [-]']
    if sum(load) < -1:
        loads[ckey] = load
    
source_matches = {"pv": "PV", "wind": "wind", "lithi": "battery discharging", "grid": "import"}
def source_translate(x):
    for key, value in source_matches.items():
        if key in x:
            return value
sources.columns = [source_translate(col) for col in sources.columns]

load_matches = {"fast": "chargers", "lith": "battery charging", "Final": "curtailment", "grid": "export"}
def load_translate(x):
    for key, value in load_matches.items():
        if key in x:
            return value
loads.columns = [load_translate(col) for col in loads.columns]


#%% plotting

supply_colors = {
    'PV': "#ebd25b", 
    'wind': "#8cc0ed" , 
    'battery discharging': "#7fc78f", 
    'import': "#f2b65c" ,
}

load_colors = {
    'chargers': "#a5c0c2", 
    'curtailment': "#454545", 
    'battery charging': "#85a0d6",
    'export': "#d18426",
}



start = 1500 # hour
duration = 7 # days
loads = loads.iloc[start:start+duration*24,:]
sources = sources.iloc[start:start+duration*24,:]

load_cm = sns.color_palette("rocket", as_cmap=True)
source_cm = sns.color_palette("crest", as_cmap=True)
opacity = .6

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6,2.2)



loads.plot.area(ax=ax, color=load_colors, alpha=opacity, linewidth=1)
sources.plot.area(ax=ax, color=supply_colors, alpha=opacity, linewidth=1)

ax.set_ylim([-15, 15])

# dt =loads.index
# xtick = {
#     loads.index[i*24]: dt.strftime("%d %B")[i*24]
#     for i in range(duration)
# }

# ax.set_xlim([loads.index[0], loads.index[duration*24-1]])
# ax.set_xticks(list(xtick.keys()))
# ax.set_xticklabels(list(xtick.values()))
# ax.xaxis.label.set_visible(False)
plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0., frameon=False)

plt.tight_layout(pad=0.3)

rc = {
    'font.family':'Open Sans',
    'font.size' : 10,
    'legend.fontsize' : 8
    }


plt.rcParams.update(rc)

ax.set_ylabel("power (GW)")

default_matplotlib_save(fig, "etm_curves.png")

# %%
