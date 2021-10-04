#%%

from LESO import System, PhotoVoltaic, PhotoVoltaicAdvanced
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from time import sleep

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
pv_advanced = PhotoVoltaicAdvanced(
    "advanced PV model", azimuth=180, tilt=40, dof=True
)
pv_ninja = PhotoVoltaic(
    "renewables.ninja", azimuth=180, tilt=40, use_ninja=True, dof=True
)

#%% add the components to the system
# note that we do not add wind now!
component_list = [pv_simple, pv_advanced]
system.add_components(component_list)
system.fetch_input_data()
system.calculate_time_series()

for c in system.components:
    print(c.name)
    print(c.state.power.sum())

#%%
tmy_years=[
    2016,
    2009,
    2007,
    2008,
    2011,
    2012,
    2009,
    2012,
    2011,
    2012,
    2007,
    2014
]
from LESO.dataservice.api import _tmy_dateparser
tmy_df = pd.read_csv("tmy.csv")
tmy_df = _tmy_dateparser(tmy_df)
gdf = tmy_df.groupby(tmy_df.index.month)
time_values = [
    (
        gdf.get_group(x).index[0].strftime("%Y-%m-%d"), 
        gdf.get_group(x).index[-1].strftime("%Y-%m-%d"),
        gdf.get_group(x).index
    ) 
    for x in gdf.groups
]

#%%

import LESO

tmp_df = pd.DataFrame(index = tmy_df.index)
for date_from, date_to, index in time_values:
    pv_ninja.date_from = date_from
    pv_ninja.date_to = date_to
    power = LESO.dataservice.api.get_renewable_ninja(pv_ninja, system.tmy, ignore_cache=True)
    tmp_df.loc[index, 'renewable.ninja'] = list(power.values)
    print("zzzz")
    sleep(10)
    

if input("Do you want to save this to a pickle?? [y/n]") == "y":
    tmp_df.to_pickle("renewable_ninja_PV_tmy.pkl")
#%%
df = pd.DataFrame(
    data=np.vstack([c.state.power.values for c in system.components]).T,
    columns=[c.name for c in system.components],
    index=pv_simple.state.index,
)
df['renewables.ninja'] = list(tmp_df.values.flatten())


agg_df = df.groupby(df.index.strftime("%B")).sum().round(0)
agg_df['renewables.ninja'] = tmp_df.groupby(df.index.strftime("%B")).sum().round(0)
agg_df.index = pd.to_datetime([f"1 {month} 2030" for month in agg_df.index])
agg_df.sort_index(inplace=True)

out_df = agg_df
out_df.index = out_df.index.strftime("%B")

#%%

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)

labels = agg_df.index.strftime("%B")
x = np.arange(len(labels))  # the label locations
width = 0.25  # the width of the bars

rects1 = ax.bar(
    x - width *1.10, 
    agg_df[pv_simple.name], 
    width, 
    label=pv_simple.name,
    color="#e1e8d3",
    edgecolor='#b4c690',
    linewidth=2,
    # alpha=0.5,
)
rects2 = ax.bar(
    x, 
    agg_df[pv_advanced.name], 
    width, 
    label=pv_advanced.name,
    color='#dae6f0',
    edgecolor='#a2c0d9',
    linewidth=2,
    # alpha=0.5,
)
rects3 = ax.bar(
    x+width*1.10, 
    agg_df[pv_ninja.name], 
    width, 
    label=pv_ninja.name,
    color='#efd2d2',
    edgecolor='#c96767',
    linewidth=2,
    # alpha=0.5,
)

ax.set_xticks(x)
ax.set_xticklabels(labels)
for tick in ax.get_xticklabels():
    tick.set_rotation(45)
ax.legend(frameon=False)
ax.set_ylabel("monthly specific \n energy yield (kWh/kWp)")


fig, ax = default_matplotlib_style(fig, ax)
default_matplotlib_save(fig, "pv_production_compare.png")


# %%
olivedrab_02 = "#e1e8d3"
olivedrab_05 = '#b4c690'

steelblue_02 = '#dae6f0'
steelblue_05 = '#a2c0d9'

firebrick_02='#efd2d2'
firebrick_05='#c96767'


fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax, subplots=2, height=2.5)
start = 600+2*24
df.iloc[start:start+24*4,:].plot(color=[olivedrab_05, steelblue_05, firebrick_05], ax=ax)
ax.set_ylabel("hourly specific \n energy yield (kWh/kWp)")
ax.set_ylim([0, 1])
ax.legend(frameon=False)
default_matplotlib_save(fig, "pv_production_typical_winterdays.png")


fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax, subplots=2, height=2.5)
start = 2800+3*24
df.iloc[start:start+24*4,:].plot(color=[olivedrab_05, steelblue_05, firebrick_05], ax=ax)
# ax.set_ylabel("hourly specific \n energy yield (kWh/kWp)")
ax.set_ylim([0, 1])
# ax.legend(loc='upper right', frameon=False, )
ax.get_legend().remove()
default_matplotlib_save(fig, "pv_production_typical_summerdays.png")




# def add_value_labels(ax, spacing=5):
#     """Add labels to the end of each bar in a bar chart.

#     Arguments:
#         ax (matplotlib.axes.Axes): The matplotlib object containing the axes
#             of the plot to annotate.
#         spacing (int): The distance between the labels and the bars.
#     """

#     # For each bar: Place a label
#     for rect in ax.patches:
#         # Get X and Y placement of label from rect.
#         y_value = rect.get_height()
#         x_value = rect.get_x()

#         # Number of points between bar and label. Change to your liking.
#         space = spacing
#         # Vertical alignment for positive values
#         va = 'bottom'

#         # If value of bar is negative: Place label below bar
#         if y_value < 0:
#             # Invert space to place label below
#             space *= -1
#             # Vertically align label at top
#             va = 'top'

#         # Use Y value as label and format number with one decimal place
#         label = "{:.0f}".format(y_value)

#         # Create annotation
#         ax.annotate(
#             label,                      # Use `label` as label
#             (x_value+0.2, y_value+1),         # Place label at end of the bar
#             xytext=(0, 6),          # Vertically shift label by `space`
#             textcoords="offset points", # Interpret `xytext` as offset in points
#             ha='center',                # Horizontally center label
#             va=va,
#             color="#c2c2c2",
#             rotation=90,
#             fontsize=8)                      # Vertically align label differently for
#                                         # positive and negative values.

# # # Call the function above. All the magic happens there.
# add_value_labels(ax)
# %%
