# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

from LESO.experiments.analysis import (
    gdatastore_results_to_df,
    gcloud_read_experiment
)
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% constants
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"

COLLECTION = "cablepooling"
RUN_ID = "2110_v2"
APPROACH = "subsidy"

force_refresh = False

pv_col = "PV South installed capacity"

#%% load in results

filename = f"{COLLECTION}_{RUN_ID}.{APPROACH}.pkl"
pickled_df = RESOURCE_FOLDER / filename

# buffer all the calculations/df, only refresh if forced to refresh
if pickled_df.exists() and not force_refresh:

    print("opened pickle -- not refreshed")
    df = pd.read_pickle(pickled_df)

else:
    filters = [
        ("run_id", "=", RUN_ID),
        ("approach", "=", APPROACH)
    ]

    df = gdatastore_results_to_df(
        collection=COLLECTION,
        filters=filters
    )

    #%% data selection
    exp = gcloud_read_experiment(
        collection=COLLECTION,
        experiment_id=df.filename_export.iat[189]
    )

    spec_yield_pv = (
        sum(exp.components.pv1.state['power [+]']) /
        exp.components.pv1.settings.installed 
    )
    tot_yield_wind = sum(exp.components.wind1.state['power [+]'])


    ## change / add some data
    df['pv_cost_absolute'] = df.pv_cost_factor * 1020
    df['curtailment'] = -df['curtailment']
    df['total_generation'] = (df[pv_col] * spec_yield_pv + tot_yield_wind)
    df['relative_curtailment'] = df['curtailment'] / df['total_generation'] *100
    df['total_installed_capacity'] = df[pv_col] + 10

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

    print("fetched data from the cloud -- refreshed")
    df.to_pickle(RESOURCE_FOLDER / filename)
#%%

subset = df[df[pv_col]!=0]
idx = subset[pv_col].argmin()
max_solar_price = subset.loc[subset.index[idx], "pv_cost_absolute"]
print(f"Solar deployment starts at: {round(max_solar_price,0)} €/kWp")

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

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_init_pv_deployment_vs_cost.png")

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

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_init_rel_curtailment_vs_deployment.png")

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

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_init_abs_curtailment_vs_deployment.png")


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

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_init_bivariate_deployment.png")
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
default_matplotlib_save(fig, IMAGE_FOLDER / "images/report_cablepool_PV_histogram.png")