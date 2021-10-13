import pandas as pd
import pandas as pd
import numpy as np
import plotly.express as pe
from pathlib import Path
import sys
import LESO
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt


from LESO.plotting import default_matplotlib_save, default_matplotlib_style


#%% data selection
df = pd.read_pickle("cablepooling_dbcheap_battery_1")

# hard-coded here for convience
spec_yield_pv = 1038.1840000000007
tot_yield_wind = 30206.649999999943
## change / add some data
pv_col = "PV South installed capacity"
bat_col = "2h battery installed capacity"
df["pv_cost_absolute"] = df.pv_cost_factor * 1020
df["curtailment"] = -df["curtailment"]
df["total_generation"] = df[pv_col] * spec_yield_pv + tot_yield_wind
df["relative_curtailment"] = df["curtailment"] / df["total_generation"] * 100
df["total_installed_capacity"] = df[pv_col] + 10


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
ax.set_ylim([-1, 35])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([380, 870])

ax.legend(frameon=False, title="Curtailment (MWh)")

default_matplotlib_save(fig, "report_cablepool_cheapbat_pv_deployment_vs_cost.png")



#%% relative curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3, 3)

sns.scatterplot(
    x="total_installed_capacity",
    y="relative_curtailment",
    hue=bat_col,
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black",
)

ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 40])

ax.set_ylabel("relative curtailment (%)")
ax.set_ylim([0, 6])
ax.legend(
    bbox_to_anchor=(0.5, -0.4),
    loc=9,
    borderaxespad=0.0,
    frameon=True,
    title="Deployed battery capacity (MWh)",
    ncol=5,
)

default_matplotlib_save(
    fig, "report_cablepool_cheapbat_rel_curtailment_vs_deployment.png"
)

#%% absolute curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3, 3)

sns.scatterplot(
    x="total_installed_capacity",
    y="curtailment",
    hue=bat_col,
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black",
)


ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 40])

ax.set_ylabel("absolute curtailment (MWh)")
ax.set_ylim([0, 3000])

ax.legend(
    bbox_to_anchor=(0.5, -0.4),
    loc=9,
    borderaxespad=0.0,
    frameon=True,
    title="Deployed battery capacity (MWh)",
    ncol=5,
)

default_matplotlib_save(
    fig, "report_cablepool_cheapbat_abs_curtailment_vs_deployment.png"
)

#%% Add battery cost for 2 hour battery


power_ref = 257
storage_ref = 277

df["battery_cost_absolute_2h"] = [
    (bcf * storage_ref * 2 + bcf * power_ref) / 2
    for bcf in df["battery_cost_factor"].values
]


#%% bi-variate scatterplot

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(5, 3)

sns.scatterplot(
    x="pv_cost_absolute",
    y="battery_cost_absolute_2h",
    size=pv_col,
    hue=pv_col,
    data=df,
    palette="dark:#5b8eb5",
    sizes=(5, 100),
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("2h battery \n capacity cost (€/kWh)")
ax.set_ylim([20, 180])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([370, 870])
ax.legend(
    bbox_to_anchor=(0.5, -0.4),
    loc=9,
    borderaxespad=0.0,
    frameon=True,
    title="Deployed PV capacity (MW)",
    ncol=6,
)

default_matplotlib_save(fig, "report_cablepool_cheapbat_bivariate_deployment.png")
#%% Battery deployment vs absolut cost scatter

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6, 2.2)
sns.scatterplot(
    x="battery_cost_absolute_2h",
    y=bat_col,
    size=pv_col,
    hue=pv_col,
    data=df,
    palette="Reds",
    ax=ax,
    edgecolor="black",
)

ax.set_ylabel("deployed battery capacity (MWh)")
ax.set_ylim([-3, 70])

ax.set_xlabel("battery capacity cost (€/kWh)")
ax.set_xlim([30, 170])
    
ax.legend(frameon=False, title="Deployed PV capacity (MW)")

default_matplotlib_save(fig, "report_cablepool_cheapbat_bat_deployment_vs_cost.png")

# %%
