#%% modules
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
APPROACH = "cheap_battery"

#%% read in data
df = get_data_from_db(
    collection=COLLECTION,
    run_id=RUN_ID,
    approach=APPROACH,
    force_refresh=False,
)
#%%
def linear_map(value, ):
    min, max = 0.41, 0.70 # @@
    map_min, map_max = 0.42, 0.81 # @@

    frac = (value - min) / (max-min)
    m_value = frac * (map_max-map_min) + map_min

    return m_value

power_ref = 257
storage_ref = 277

df["battery_cost_absolute_6h"] = [
    (bcf * storage_ref * 6 + linear_map(bcf) * power_ref) / 6
    for bcf in df["battery_cost_factor"].values
]


#%% PV deployment vs absolut cost scatter

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 2.5)
sns.scatterplot(
    x="pv_cost_absolute",
    y=pv_col,
    size=total_bat_col,
    hue=total_bat_col,
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("deployed PV capacity (MW)")
ax.set_ylim([-1, 45])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([380, 870])

ax.legend(frameon=False, title="deployed battery\ncapacity (MWh)")

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_cheapbat_pv_deployment_vs_cost.png")



#%% relative curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3, 3)

sns.scatterplot(
    x="total_installed_capacity",
    y="relative_curtailment",
    hue=total_bat_col,
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black",
)

ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 55])

ax.set_ylabel("relative curtailment (%)")

ax.legend(
    bbox_to_anchor=(0.5, -0.35),
    loc=9,
    borderaxespad=0.0,
    frameon=True,
    title="deployed battery capacity (MWh)",
    ncol=3,
)

default_matplotlib_save(
    fig, IMAGE_FOLDER / "report_cablepool_cheapbat_rel_curtailment_vs_deployment.png"
)

relplot_ticks = ax.get_xticks()
relplot_labels = ax.get_xticklabels()

#%% absolute curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3, 3)

sns.scatterplot(
    x="total_installed_capacity",
    y="curtailment",
    hue=total_bat_col,
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black",
)


ax.set_xlabel("total deployed capacity (MW)")
ax.set_xticks(relplot_ticks)
ax.set_xticklabels(relplot_labels)
ax.set_xlim([0, 55])

ax.set_ylabel("curtailment (MWh)")
ax.set_ylim([-100, 3000])

ax.legend(
    bbox_to_anchor=(0.5, -0.35),
    loc=9,
    borderaxespad=0.0,
    frameon=True,
    title="deployed battery capacity (MWh)",
    ncol=3,
)

default_matplotlib_save(
    fig, IMAGE_FOLDER / "report_cablepool_cheapbat_abs_curtailment_vs_deployment.png"
)

#%% bi-variate scatterplot 1

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(5, 3)

sns.scatterplot(
    x="pv_cost_absolute",
    y="battery_cost_absolute_6h",
    size=pv_col,
    hue=pv_col,
    data=df,
    palette="Reds",
    sizes=(5, 100),
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("6h battery \n capacity cost (€/kWh)")
ax.set_xlim([25, 135])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([370, 870])
ax.legend(
    bbox_to_anchor=(0.5, -0.4),
    loc=9,
    borderaxespad=0.0,
    frameon=True,
    title="deployed PV capacity (MW)",
    ncol=6,
)

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_cheapbat_bivariate_deployment.png")

#%% bi-variate scatterplot 1

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(5, 3)

sns.scatterplot(
    x="pv_cost_absolute",
    y="battery_cost_absolute_6h",
    size=total_bat_col,
    hue=total_bat_col,
    data=df,
    palette="Reds",
    sizes=(5, 100),
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("6h battery \n capacity cost (€/kWh)")
ax.set_xlim([25, 135])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([370, 870])
ax.legend(
    bbox_to_anchor=(0.5, -0.4),
    loc=9,
    borderaxespad=0.0,
    frameon=True,
    title="battery deployed capacity (MWh)",
    ncol=6,
)

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_cheapbat_bivariate_deployment2.png")
#%% Battery deployment vs absolut cost scatter

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 2.5)
sns.scatterplot(
    x="battery_cost_absolute_6h",
    y=total_bat_col,
    size=pv_col,
    hue=pv_col,
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("deployed battery\ncapacity (MWh)")
ax.set_ylim([-3, 100])

ax.set_xlabel("6h battery capacity cost (€/kWh)")
ax.set_xlim([25, 135])
    
ax.legend(frameon=False, title="deployed PV capacity (MW)")

default_matplotlib_save(fig, IMAGE_FOLDER / "report_cablepool_cheapbat_bat_deployment_vs_cost.png")