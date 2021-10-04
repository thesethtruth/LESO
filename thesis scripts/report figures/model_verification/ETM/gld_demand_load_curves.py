#%% ---------------------------------
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from time import sleep
import seaborn as sns
from matplotlib import cm

from LESO.plotting import default_matplotlib_save, default_matplotlib_style


#%% ---------------------------------

df = pd.read_csv("gld_curve_export.csv", index_col=0)
cols = df.abs().sum(axis=0).sort_values().index[-10:]

not_cols = [col for col in df.columns if col not in cols]

loads = pd.DataFrame(index=df.index)
sources = pd.DataFrame(index=df.index)
rest_loads = loads.copy(deep=True)
rest_sources = sources.copy(deep=True)

for col in df.columns:
    
    if col in cols:
        if "input" in col:
            loads[col] = - df[col]
        else:
            sources[col] = df[col]
    else:
        if "input" in col:
            rest_loads[col] = - df[col]
        else:
            rest_sources[col] = df[col]
loads['other loads'] = rest_loads.sum(axis=1).values
sources['other sources'] = rest_sources.sum(axis=1).values

start = 3000 # hour
duration = 7 # days
loads = loads.iloc[start:start+duration*24,:]/1000
sources = sources.iloc[start:start+duration*24,:]/1000

loads.columns = [
    col.replace(".input (MW)", "").replace(".output (MW)", "").replace("_", " ")
    for col in loads.columns
]
loads.columns = [
    "Agriculture",
    "Commercial buildings",
    "Export",
    "Household appliances",
    "Food industry",
    "Ohter loads"
]

sources.columns = [
    col.replace(".input (MW)", "").replace(".output (MW)", "").replace("_", " ")
    for col in sources.columns
]
sources.columns = [
    "Rooftop PV solar",
    "Import",
    "Centralized PV solar",
    "On-shore wind turbine",
    "Residential PV solar",
    "Other sources"
]

#%% ---------------------------------

load_cm = sns.color_palette("rocket", as_cmap=True)
source_cm = sns.color_palette("crest", as_cmap=True)
opacity = 0.7

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6,2.2)

loads.plot.area(ax=ax, cmap=load_cm, alpha=opacity)
sources.plot.area(ax=ax, cmap=source_cm, alpha=opacity)
ax.set_ylim([-3.5, 3.5])

dt = pd.to_datetime(loads.index)
xtick = {
    i*24: dt.strftime("%d %B")[i*24]
    for i in range(duration)
}
ax.xaxis.label.set_visible(False)
ax.set_xlim([0, duration*24-1])
ax.set_xticks(list(xtick.keys()))
ax.set_xticklabels(list(xtick.values()))
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
from LESO.defaultvalues import generation_whitelist
from LESO.dataservice.api import _get_etm_curve

etm_output = _get_etm_curve(
    815716,
    generation_whitelist = None
)

leso_input = _get_etm_curve(
    815716,
    generation_whitelist = generation_whitelist
)

#%%

df = pd.DataFrame(
    data = np.array([etm_output, leso_input]).T,
    columns = ["ETM scenario demand curve", "LESO input residual curve"],
    index = rest_loads.index
)

# %%
subset = df.iloc[start:start+duration*24,:]/1000


fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6,2.2)

subset.plot(
    color=['steelblue', 'firebrick'],
    ax=ax,
    style=['--', '-'],
    linewidth=2
)
plt.axhline(0, color='darkgrey')
ax.legend(frameon=False, ncol=2)
ax.set_ylim([-2, 0.5])
ax.set_ylabel("power (GW)")
ax.xaxis.label.set_visible(False)
ax.set_xlim([0, duration*24-1])
ax.set_xticks(list(xtick.keys()))
ax.set_xticklabels(list(xtick.values()))


default_matplotlib_save(fig, "etm_residuals.png")


# %%
