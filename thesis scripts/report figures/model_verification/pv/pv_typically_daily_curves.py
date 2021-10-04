#%% ---------------------------------
from pandas.core.indexes.datetimes import date_range
from pandas.tseries import frequencies
from LESO import System, PhotoVoltaic
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from time import sleep
import seaborn as sns

from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% ---------------------------------
# Define system and components
modelname = "verification"
lat, lon = 51.81, 5.84  # Nijmegen

# initiate System component
system = System(lat=lat, lon=lon, model_name=modelname)

# initiate and define components
pv_ninja = PhotoVoltaic(
    "simple PV model", azimuth=180, tilt=40, use_ninja=True, dof=True
)
pv_simple = PhotoVoltaic(
    "simple PV model", azimuth=180, tilt=40, use_ninja=False, dof=True
)


component_list = [pv_simple, pv_ninja]
system.add_components(component_list)
system.fetch_input_data()
system.calculate_time_series()


#%% ---------------------------------
power = pv_ninja.state.power
gdf = power.groupby(power.index.month)
groups = [gdf.get_group(x) for x in gdf.groups]
power_per_day = pd.DataFrame(
    data = np.array([group.groupby(group.index.hour).mean().values.flatten() for group in groups]).T,
    columns= [group.index.strftime("%B")[0] for group in groups],
    index=pd.date_range(
        "01/01/2030",
        periods=24,
        freq='h'
    )
)


#%% ---------------------------------


fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6,2.2)
sns.lineplot(
    data=power_per_day,
    alpha=0.7,
    palette="ocean",
    ax=ax
)
ax.legend(frameon=False,ncol=2)
xtick = {
    power_per_day.index[2+i*4]: power_per_day.index.strftime("%H:%M")[2+i*4]
    for i in range(6)
}

ax.set_xticks(list(xtick.keys()))
ax.set_xticklabels(list(xtick.values()))

ax.set_ylabel("hourly specific \n energy yield (kWh/kWp)")
ax.set_ylim([0,0.7])
default_matplotlib_save(fig, "pv_yield_per_month.png")

# %%

tilts = [i*10 for i in range(10)]
tilt_powers = []
for tilt in tilts:
    pv_simple.tilt = tilt
    pv_simple.calculate_time_serie(system.tmy)
    tilt_power = pv_simple.state.power
    tilt_power = tilt_power.groupby(tilt_power.index.hour).mean()
    tilt_powers.append(tilt_power.values.flatten())

tilt_powers = np.array(tilt_powers)
power_per_tilt = pd.DataFrame(
    data = tilt_powers.T,
    columns= [f"{tilt}"+r"$^{\circ}$ tilt" for tilt in tilts],
    index=pd.date_range(
        "01/01/2030",
        periods=24,
        freq='h'
    )
)

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6,2.2)
sns.lineplot(
    data=power_per_tilt,
    alpha=0.7,
    palette="ocean",
    ax=ax
)
ax.legend(frameon=False,ncol=2)
xtick = {
    power_per_day.index[2+i*4]: power_per_day.index.strftime("%H:%M")[2+i*4]
    for i in range(6)
}

ax.set_xticks(list(xtick.keys()))
ax.set_xticklabels(list(xtick.values()))

ax.set_ylabel("hourly specific \n energy yield (kWh/kWp)")
ax.set_ylim([0,0.4])
default_matplotlib_save(fig, "pv_yield_per_tilt.png")

# %%
