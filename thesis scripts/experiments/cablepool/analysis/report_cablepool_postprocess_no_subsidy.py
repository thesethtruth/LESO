import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from LESO.plotting import default_matplotlib_save, default_matplotlib_style


#%% data selection
df = pd.read_pickle("cablepooling_dbno_subsidy_1")

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
switch = lambda x: "<1" if x<1 else ">1"
df["ratio"] = [switch(x) for x in df[pv_col] / 10]


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

default_matplotlib_save(fig, "report_cablepool_no_sub_pv_deployment_vs_cost.png")


#%% relative curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,3.5)

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
ax.set_ylim([20, 23])

ax.legend(
    bbox_to_anchor=(0.5, -0.4),
    loc=9,
    frameon=True,
    title="Ratio solar-to-wind",
    ncol=2,
)

default_matplotlib_save(fig, "report_cablepool_no_sub_rel_curtailment_vs_deployment.png")

#%% absolute curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,3)

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
ax.set_ylim([6500, 11000])

ax.legend(
    bbox_to_anchor=(0.5, -0.4),
    loc=9,
    frameon=True,
    title="Ratio solar-to-wind",
    ncol=2,
)

default_matplotlib_save(fig, "report_cablepool_no_sub_abs_curtailment_vs_deployment.png")

# %%
