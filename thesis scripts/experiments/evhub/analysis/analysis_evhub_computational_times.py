# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

from LESO.experiments.analysis import gdatastore_results_to_df, gcloud_read_experiment
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% constants
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"

COLLECTION = "evhub"
RUN_ID = "2110_v2"

force_refresh = True

## pointers
pv_col = "PV South installed capacity"
wind_col = "Nordex N100 2500 installed capacity"
bat2_col = "2h battery installed capacity"
bat6_col = "6h battery installed capacity"
bat10_col = "10h battery installed capacity"

batcols = [bat2_col, bat6_col, bat10_col]

#%% load in results

filename = f"{COLLECTION}_{RUN_ID}.pkl"
pickled_df = RESOURCE_FOLDER / filename

# buffer all the calculations/df, only refresh if forced to refresh
if pickled_df.exists() and not force_refresh:

    print("opened pickle -- not refreshed")
    db = pd.read_pickle(pickled_df)

else:

    db = gdatastore_results_to_df(
        collection=COLLECTION,
    )

    ## needed for more kpis
    spec_yield_pv = 1025.307
    spec_yield_wind = 2937.6

    ## change / add some data
    db["pv_cost_absolute"] = db.pv_cost_factor * 1020
    db["wind_cost_absolute"] = db.wind_cost_factor * 1350
    db["curtailment"] = -db["curtailment"]
    db["total_generation"] = db[pv_col] * spec_yield_pv + db[wind_col] * spec_yield_wind
    db["relative_curtailment"] = db["curtailment"] / db["total_generation"] * 100
    db["total_installed_capacity"] = db[pv_col] + db[wind_col]
    db["total_storage_energy"] = db[batcols].sum(axis=1)
    db["total_storage_power"] = db[bat2_col] / 2 + db[bat6_col] / 6 + db[bat10_col] / 10

    def linear_map(
        value,
    ):
        min, max = 0.41, 0.70  # @@
        map_min, map_max = 0.42, 0.81  # @@

        frac = (value - min) / (max - min)
        m_value = frac * (map_max - map_min) + map_min

        return m_value

    power_ref = 257
    storage_ref = 277

    db["battery_cost_absolute_2h"] = [
        (bcf * storage_ref * 2 + linear_map(bcf) * power_ref) / 2
        for bcf in db["battery_cost_factor"].values
    ]

    db.to_pickle(RESOURCE_FOLDER / filename)
    print("requested data from the server -- refreshed the pickle")

## data selection


#%%

run_id = "2110_v2"
df = db.query(f"run_id == '{run_id}'")

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 2.2)
sns.scatterplot(
    x=df.index,
    y="solving_time",
    hue="grid_capacity",
    data=df,
    palette="Blues",
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("Solving time (s)")
# ax.set_ylim([-1, 20])

ax.set_xlabel("")
# ax.set_xlim([380, 870])

l = ax.legend(
    bbox_to_anchor=(1.02, 0.5),
    loc=6,
    borderaxespad=0.0,
    frameon=True,
    title="Grid \ncapacity (MW)",
)
plt.setp(l.get_title(), multialignment="center")

default_matplotlib_save(
    fig, IMAGE_FOLDER / f"analysis_evhub_computational_times_{run_id}.png"
)


# %%

run_id = "2210_v2"
df = db.query(f"run_id == '{run_id}'")

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 2.2)
sns.scatterplot(
    x=df.index,
    y="solving_time",
    hue="grid_capacity",
    data=df,
    palette="Blues",
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("Solving time (s)")
# ax.set_ylim([-1, 20])

ax.set_xlabel("")
# ax.set_xlim([380, 870])

l = ax.legend(
    bbox_to_anchor=(1.02, 0.5),
    loc=6,
    borderaxespad=0.0,
    frameon=True,
    title="Grid \ncapacity (MW)",
)
plt.setp(l.get_title(), multialignment="center")

default_matplotlib_save(
    fig, IMAGE_FOLDER / f"analysis_evhub_computational_times_{run_id}.png"
)
#%% swarm plot
sns.set_palette(sns.color_palette(["#b7094c","#892b64","#5c4d7d","#2e6f95"]))
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 4)


# sns.stripplot(x="solving_time", y="grid_capacity", data=df, ax=ax, orient='h', size=2, alpha=.3, jitter=.5, edgecolor="black", palette="dark:#69d_r")
sns.swarmplot(
    x="solving_time",
    y="grid_capacity",
    data=df,
    ax=ax,
    orient="h",
    size=1.5,
    alpha=0.5,
    # hue="total_storage_energy",
    edgecolor="black",
)

ax.set_ylabel("grid capacity")
ax.set_xlabel("solving time (s)")


default_matplotlib_save(
    fig, IMAGE_FOLDER / f"analysis_evhub_computational_times_{run_id}_swarmplot.png"
)

#%% strip plot
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 3)


sns.stripplot(
    x="solving_time",
    y="grid_capacity",
    data=df,
    ax=ax,
    orient="h",
    size=2,
    alpha=.5,
    jitter=0.4,
    edgecolor="black",
)

ax.set_ylabel("grid capacity")
ax.set_xlabel("solving time (s)")


default_matplotlib_save(
    fig, IMAGE_FOLDER / f"analysis_evhub_computational_times_{run_id}_stripplot.png"
)


#%% violin plot
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 3)


sns.boxplot(
    x="solving_time",
    y="grid_capacity",
    data=df,
    ax=ax,
    orient="h",
)

ax.set_ylabel("grid capacity")
ax.set_xlabel("solving time (s)")


default_matplotlib_save(
    fig, IMAGE_FOLDER / f"analysis_evhub_computational_times_{run_id}_boxplot.png"
)