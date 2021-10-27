import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

from cablepool_postprocess_tools import (
    get_data_from_db,
    gcloud_read_experiment,
    pv_col,
    wind_col,
    bat2_col,
    bat6_col,
    bat10_col,
    total_bat_col,
    batcols
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

#%% read in data
df = get_data_from_db(
    collection=COLLECTION,
    run_id=RUN_ID,
    approach=APPROACH,
    force_refresh=False,
    # filter=filter,
)

exp = gcloud_read_experiment(
    collection=COLLECTION,
    experiment_id=df.filename_export.iat[189]
)

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

ax.set_ylabel("deployed PV\ncapacity (MW)")
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

ax.set_ylabel("deployed PV\ncapacity (MW)")
ax.set_ylim([-1, 20])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([380, 870])

ax.legend(frameon=False, title="Subsidy scheme")

default_matplotlib_save(
    fig, IMAGE_FOLDER / "report_cablepool_pv_deployment_vs_cost_subsidy_compare.png"
)
# %%
