#%%

from LESO import System, PhotoVoltaic, PhotoVoltaicAdvanced
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
pv_simple = PhotoVoltaic(
    "simple PV model", azimuth=180, tilt=40, use_ninja=False, dof=True
)
pv_advanced = PhotoVoltaicAdvanced("advanced PV model", azimuth=180, tilt=40, dof=True)
pv_ninja = PhotoVoltaic(
    "renewables.ninja", azimuth=180, tilt=40, use_ninja=True, dof=True
)

#%% add the components to the system
# note that we do not add wind now!
component_list = [pv_simple, pv_advanced, pv_ninja]
system.add_components(component_list)
system.fetch_input_data()
system.calculate_time_series()


start = 190
for c in system.components:
    print(c.name)
    print(c.state.power.sum())
    # c.state.power[start * 24 : (start + 1) * 24].plot()

#%%


df = pd.DataFrame(
    data=np.vstack([c.state.power.values for c in system.components]).T,
    columns=[c.name for c in system.components],
    index=pv_simple.state.index,
)

sdf = df.drop("renewables.ninja", axis=1)
# %%
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)


agg_df = sdf.groupby(sdf.index.strftime("%B")).sum().round(0)
agg_df.index = pd.to_datetime([f"1 {month} 2030" for month in agg_df.index])
agg_df.sort_index(inplace=True)
labels = agg_df.index.strftime("%B")


x = np.arange(len(labels))  # the label locations
width = 0.35  # the width of the bars

rects1 = ax.bar(
    x - width / 2, 
    agg_df[pv_simple.name], 
    width, 
    label=pv_simple.name,
    color="olivedrab",
    edgecolor='olivedrab',
    linewidth=2,
    alpha=0.2,
)
rects2 = ax.bar(
    x + width / 2, 
    agg_df[pv_advanced.name], 
    width, 
    label=pv_advanced.name,
    color='steelblue',
    edgecolor='steelblue',
    linewidth=2,
    alpha=0.2,
)

ax.set_xticks(x)
ax.set_xticklabels(labels)
for tick in ax.get_xticklabels():
    tick.set_rotation(45)
ax.legend(frameon=False)
ax.set_ylabel("monthly specific \n energy yield (kWh/kWp)")

ax.bar_label(rects1, padding=6, color="#c2c2c2", fontsize=8, rotation=90)
ax.bar_label(rects2, padding=6, color="#c2c2c2", fontsize=8, rotation=90)



fig, ax = default_matplotlib_style(fig, ax)
default_matplotlib_save(fig, "pv_production_compare.png")


# %%
