# %%
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import LESO
import seaborn as sns
import matplotlib.pyplot as plt

from LESO.experiments.analysis import (
    load_ema_leso_results,
    open_leso_experiment_file,
)
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% constants
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
sys.path.append(FOLDER.parent.absolute().__str__())
run_id = 210907

#%% load in results
experiments, outcomes, df = load_ema_leso_results(
    run_id=run_id, 
    exp_prefix="cablepooling",
    results_folder=RESULT_FOLDER)

#%% data selection
df = df.query("subsidy_scheme == 'brownfield'").copy(deep=True)
exp = open_leso_experiment_file(RESULT_FOLDER / df.filename_export.iat[189])

spec_yield_pv = (
    sum(exp.components.pv1.state['power [+]']) /
    exp.components.pv1.settings.installed 
)
tot_yield_wind = sum(exp.components.wind1.state['power [+]'])

## change / add some data
pv_col = "PV South installed capacity"
df['pv_cost_absolute'] = df.pv_cost_factor * 1020
df['curtailment'] = -df['curtailment']
df['total_generation'] = (df[pv_col] * spec_yield_pv + tot_yield_wind)
df['relative_curtailment'] = df['curtailment'] / df['total_generation'] *100
df['total_installed_capacity'] = df[pv_col] + 10



#%% Deployment vs absolut cost scatter

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6,2.2)
sns.scatterplot(
    x="pv_cost_absolute",
    y=pv_col,
    size='curtailment',
    hue='curtailment',
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black"
)

ax.set_ylabel("deployed PV capacity (MW)")
ax.set_ylim([-1, 20])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([380, 870])

ax.legend(frameon=False, title='Curtailment (MWh)')

default_matplotlib_save(fig, "report_cablepool_init_pv_deployment_vs_cost.png")

#%% relative curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,2.2)

sns.lineplot(
    x="total_installed_capacity",
    y="relative_curtailment",
    # size='curtailment',
    # hue='curtailment',
    data=df,
    color="firebrick",
    ax=ax,
    # edgecolor="black"
)

ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 40])

ax.set_ylabel("relative curtailment (%)")
ax.set_ylim([0, 6])

default_matplotlib_save(fig, "report_cablepool_init_rel_curtailment_vs_deployment.png")

#%% absolute curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,2.2)

sns.lineplot(
    x="total_installed_capacity",
    y="curtailment",
    # size='curtailment',
    # hue='curtailment',
    data=df,
    color='steelblue',
    ax=ax,
    # edgecolor="black"
)

ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 40])

ax.set_ylabel("absolute curtailment (MWh)")
ax.set_ylim([0, 3000])

default_matplotlib_save(fig, "report_cablepool_init_abs_curtailment_vs_deployment.png")

#%% Add battery cost for 2 hour battery

def linear_map(value, ):
    min, max = 0.41, 0.70 # @@
    map_min, map_max = 0.42, 0.81 # @@

    frac = (value - min) / (max-min)
    m_value = frac * (map_max-map_min) + map_min

    return m_value

power_ref = 257
storage_ref = 277

df["battery_cost_absolute_2h"] = [
    (bcf * storage_ref *2 + linear_map(bcf)*power_ref)/2
    for bcf in df["battery_cost_factor"].values
]


#%% bi-variate scatterplot

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(5,3)

sns.scatterplot(
    x="pv_cost_absolute",
    y="battery_cost_absolute_2h",
    size=pv_col,
    hue=pv_col,
    data=df,
    palette="Reds",
    sizes=(10, 40),
    ax=ax,
    edgecolor="black"
)

ax.set_ylabel("2h battery \n capacity cost (€/kWh)")
ax.set_ylim([160, 310])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([370, 870])
ax.legend(bbox_to_anchor=(0.5, -.4), loc=9, borderaxespad=0., frameon=True, title='Deployed PV capacity (MW)',ncol=6)

default_matplotlib_save(fig, "report_cablepool_init_bivariate_deployment.png")
# %%
timeseries = exp.components.pv1.state["power [+]"]
timeseries = [i/max(timeseries) for i in timeseries]

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(4,2)
ax.hist(
    timeseries,
    color='firebrick',
    alpha=0.5,
    bins=30,
)
ax.legend(frameon=False)
ax.set_ylabel("frequency [h/y]")
ax.set_ylim([0,500])
ax.set_xlabel("capacity factor [-]")
ax.set_xlim([0,1])
default_matplotlib_save(fig, "images/report_cablepool_PV_histogram.png")