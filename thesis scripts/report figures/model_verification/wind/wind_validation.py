from LESO import System, Wind
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% Define system and components
modelname = "verification"
lat, lon = 51.81, 5.84  # Nijmegen

# initiate System component
system = System(lat=lat, lon=lon, model_name=modelname)

# initiate and define components
wind_pvgis = Wind(
    "wind based on PVGIS",
    turbine_type="V90/2000",  # turbine type as in oedb turbine library
    hub_height=100,  # in m
    installed=1,
)
wind_ninja = Wind(
    "wind renewables.ninja", 
    use_ninja=True,
    turbine_type = "Vestas V90 2000",
    hub_height=100,  # in
    installed=1,
)

system.add_components([wind_pvgis, wind_ninja])
tmy_2015 = pd.read_csv("wind_2015.csv")
system.fetch_input_data()
system.tmy.WS = tmy_2015.WS10m.values
system.tmy.T = tmy_2015.T2m.values

system.calculate_time_series()

#%%

df = pd.DataFrame(
    data=np.vstack([c.state.power.values for c in system.components]).T,
    columns=[c.name for c in system.components],
    index=wind_pvgis.state.index,
)


agg_df = df.groupby(df.index.strftime("%B")).sum().round(0)
agg_df.index = pd.to_datetime([f"1 {month} 2030" for month in agg_df.index])
agg_df.sort_index(inplace=True)
out_df = agg_df
out_df.index = out_df.index.strftime("%B")

#%%
from LESO.plotting import steelblue_05, steelblue_02, firebrick_05, firebrick_02

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

labels = agg_df.index.strftime("%B")
x = np.arange(len(labels))  # the label locations
width = 0.35  # the width of the bars

rects1 = ax.bar(
    x - width/2, 
    agg_df[wind_pvgis.name], 
    width, 
    label=wind_pvgis.name,
    color=steelblue_02,
    edgecolor=steelblue_05,
    linewidth=2,
)
rects2 = ax.bar(
    x + width/2, 
    agg_df[wind_ninja.name], 
    width, 
    label=wind_ninja.name,
    color=firebrick_02,
    edgecolor=firebrick_05,
    linewidth=2,
)

ax.set_xticks(x)
ax.set_xticklabels(labels)
for tick in ax.get_xticklabels():
    tick.set_rotation(45)
ax.legend(frameon=False)
ax.set_ylabel("monthly specific \n energy yield (kWh/kWp)")


fig, ax = default_matplotlib_style(fig, ax)
default_matplotlib_save(fig, "wind_production_compare.png")

# %%

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax, subplots=2, height=2.5)
start = 600+2*24
df.iloc[start:start+24*4,:].plot(color=[steelblue_05, firebrick_05], ax=ax)
ax.set_ylabel("hourly specific \n energy yield (kWh/kWp)")
ax.set_ylim([0, 1.05])
ax.get_legend().remove()
default_matplotlib_save(fig, "wind_production_typical_winterdays.png")


fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax, subplots=2, height=2.5)
start = 2800+3*24
df.iloc[start:start+24*4,:].plot(color=[steelblue_05, firebrick_05], ax=ax)
# ax.set_ylabel("hourly specific \n energy yield (kWh/kWp)")
ax.set_ylim([0, 1.05])
# ax.legend(loc='upper right', frameon=False, )
ax.get_legend().remove()
ax.legend(loc='upper right', frameon=False)
default_matplotlib_save(fig, "wind_production_typical_summerdays.png")
# %%

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(4,2)
ax.hist(
    wind_ninja.state,
    color='firebrick',
    alpha=0.5,
    bins=30,
    label=wind_ninja.name
)
ax.hist(
    wind_pvgis.state,
    color='steelblue',
    alpha=0.5,
    bins=30,
    label=wind_pvgis.name
)
ax.legend(frameon=False)
ax.set_ylabel("frequency [h/y]")
ax.set_xlabel("capacity factor [-]")
ax.set_xlim([0,1])
default_matplotlib_save(fig, "wind_histogram.png")

# %%
