import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

from LESO.experiments.analysis import (
    gdatastore_results_to_df,
)
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% constants
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"

COLLECTION = "cablepooling"
RUN_ID = "2110_v2"
APPROACH = "no_subsidy"

force_refresh = False

filename = f"{COLLECTION}_{RUN_ID}.{APPROACH}.pkl"
pickled_df = RESOURCE_FOLDER / filename

pv_col = "PV South installed capacity"
wind_col = "Nordex N100 2500 installed capacity"
bat_col = "2h battery installed capacity"

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

    # hard-coded here for convience
    spec_yield_pv = 1038.1840000000007
    tot_yield_wind = 30206.649999999943


    ## change / add some data
    df["pv_cost_absolute"] = df.pv_cost_factor * 1020
    df["curtailment"] = -df["curtailment"]
    df["total_generation"] = df[pv_col] * spec_yield_pv + tot_yield_wind
    df["relative_curtailment"] = df["curtailment"] / df["total_generation"] * 100
    df["total_installed_capacity"] = df[pv_col] + 10
    switch = lambda x: "<1" if x < 1 else ">1"
    df["ratio"] = [switch(x) for x in df[pv_col] / 10]

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

#%% PV deployment vs absolut cost scatter

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 2.2)
sns.scatterplot(
    x="pv_cost_absolute",
    y=pv_col,
    size="curtailment",
    hue="curtailment",
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("deployed PV capacity (MW)")
ax.set_ylim([-1, 20])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([380, 870])

ax.legend(frameon=False, title="Curtailment (MWh)")

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_no_sub_pv_deployment_vs_cost.png")


#%%
idx = df["relative_curtailment"].argmin()
min_curtailment_ratio = df[pv_col].iat[idx] / df[wind_col].iat[idx]
print(f"Minimal curtailment ratio: {round(min_curtailment_ratio*100,0)} ")

#%% relative curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3, 3)

df.sort_values("ratio", inplace=True)
sns.scatterplot(
    x="total_installed_capacity",
    y="relative_curtailment",
    hue="ratio",
    data=df,
    palette="coolwarm",
    ax=ax,
    edgecolor="black",
)


ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 30])

ax.set_ylabel("relative curtailment (%)")
ax.set_ylim([23, 26])

ax.legend(
    bbox_to_anchor=(0.5, -0.3),
    loc=9,
    frameon=True,
    title="Ratio solar-to-wind",
    ncol=2,
)

default_matplotlib_save(
    fig, IMAGE_FOLDER / "report_cablepool_no_sub_rel_curtailment_vs_deployment.png"
)

#%% absolute curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3, 3)

sns.scatterplot(
    x="total_installed_capacity",
    y="curtailment",
    hue="ratio",
    data=df,
    palette="coolwarm",
    ax=ax,
    edgecolor="black",
)

ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 30])

ax.set_ylabel("curtailment (MWh)")
ax.set_ylim([7500, 12000])

ax.legend(
    bbox_to_anchor=(0.5, -0.3),
    loc=9,
    frameon=True,
    title="Ratio solar-to-wind",
    ncol=2,
)

default_matplotlib_save(
    fig, IMAGE_FOLDER / "report_cablepool_no_sub_abs_curtailment_vs_deployment.png"
)

# plt.tight_layout(pad=0.3)
# plt.savefig("report_cablepool_no_sub_abs_curtailment_vs_deployment_alt.png", dpi=300, bbox_inches='tight', pad_inches=0)

# %% whole lotta stuff to get the original cable pooling results

approach = "subsidy"
filename = f"{COLLECTION}_{RUN_ID}.{approach}.pkl"
pickled_df = RESOURCE_FOLDER / filename

df2 = pd.read_pickle(pickled_df)

#%%
from LESO.plotting import steelblue_05, firebrick_02, firebrick_05

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 2.2)
ax.plot(
    df["pv_cost_absolute"],
    df[pv_col],
    'o',
    markersize=6,
    markerfacecolor=steelblue_05,
    markeredgecolor="black",
    markeredgewidth=0.5,
    label='No subsidy'
)
ax.plot(
    df2["pv_cost_absolute"],
    df2[pv_col],
    'o',
    markersize=6,
    markerfacecolor=firebrick_05,
    markeredgecolor="black",
    markeredgewidth=0.5,
    label='Fixed-support subsidy'
)

ax.set_ylabel("deployed PV capacity (MW)")
ax.set_ylim([-1, 20])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([380, 870])

ax.legend(frameon=False, title="Subsidy scheme")

default_matplotlib_save(
    fig, IMAGE_FOLDER / "report_cablepool_pv_deployment_vs_cost_subsidy_compare.png"
)
# %%
