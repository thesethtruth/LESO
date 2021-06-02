# pvlibexplore.py
import pandas as pd
import pvlib
from LESO.feedinfunctions import PVlibweather
from LESO.feedinfunctions import bifacial
import matplotlib.pyplot as plt

from LESO import System
from LESO import PhotoVoltaic, PhotoVoltaicAdvanced, BifacialPhotoVoltaic

pv1 =           PhotoVoltaic('simplePV')
pv2 =           PhotoVoltaicAdvanced('advancedPV')
pv3 =           PhotoVoltaicAdvanced('trackingPV-NS', tracking=True)
pv4 =           PhotoVoltaicAdvanced('trackingPV2-EW', tracking=True, azimuth=-90)
pv5 =           BifacialPhotoVoltaic('bifacialPV')

filename = 'Trial to compare'
system = System(52, 5, model_name = filename)
system.add_components([pv1, pv2, pv3, pv4, pv5])
system.fetch_input_data()
system.calculate_time_series()

for pv in system.components:
    print(f'{pv.name}: {pv.state.power.sum()/pv.installed} kWh / ( year * kWp )')


# cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
# cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')

# huawei = list()
# for col in cec_inverters.columns:
#     if 'Hua' in col:
#         huawei.append(col)

# jinko = list()
# for col in cec_modules.columns:
#     if 'Jinko' in col:
#         jinko.append(col)

# jinko_example = cec_modules['Jinko_Solar_Co___Ltd_JKM350M_72_V']


#%%
PV = pv5
tmy = system.tmy

# get weather in correct format
weather = PVlibweather(tmy)
# define site location for getting solar positions    
tmy.site = pvlib.location.Location(tmy.lat, tmy.lon, tmy.tz)
# Get solar azimuth and zenith to pass to the transposition function
sun = tmy.site.get_solarposition(times=tmy.index)
# utility dataframe to supply arguments in correct dimensions
setup = pd.DataFrame(index=tmy.index)
setup['azimuth'] = 90
setup['tilt'] = 90
setup['axis'] = 0

poa_front, poa_back, front, back = pvlib.bifacial.pvfactors_timeseries( solar_azimuth=sun.azimuth,
                                                solar_zenith=sun.zenith,
                                                surface_azimuth=setup.azimuth,
                                                surface_tilt=setup.tilt,
                                                axis_azimuth=setup.axis,
                                                timestamps=tmy.index,
                                                dni=weather.dni,
                                                dhi=weather.dhi,
                                                gcr=0.55,
                                                pvrow_height=2,
                                                pvrow_width=4,
                                                albedo=0.23,
                                                n_pvrows=3,
                                                index_observed_pvrow=1,
                                                rho_front_pvrow=0.03,
                                                rho_back_pvrow=0.05,
                                                horizon_band_angle=15.0)

front.index, back.index = PV.state.index, PV.state.index

front.fillna(0, inplace=True)
back.fillna(0, inplace=True)
effective = front + back*PV.bifacial_factor
poa = poa_front
bifacial_irradiance = pd.DataFrame(index=PV.state.index)
bifacial_irradiance['effective_irradiance'] = pd.Series(effective, index = PV.state.index)
bifacial_irradiance['poa_global'] = pd.Series(poa.values, index=PV.state.index)
bifacial_irradiance['wind_speed'] = pd.Series(tmy['WS10m'].values, index = PV.state.index)
bifacial_irradiance['temp_air'] = pd.Series(tmy['T2m'].values, index = PV.state.index)

# %%
import numpy as np
import seaborn as sns
system.components[0].sum_by_month()

fig = plt.figure(figsize=(12,5))
i = 0.
r = np.arange(len(system.components[0].monthly_state.index))
barwidth = .2
colors = sns.color_palette('Set3', len(system.components))

for i, component in enumerate(system.components):
    component.sum_by_month()
    plt.bar(
        r, 
        list(component.monthly_state.values.flatten()), 
        label = component.name,
        width=barwidth,
        alpha = 1,
        color = colors[i]
    )
    plt.legend()
    r = [x + barwidth for x in r]

plt.xticks([x - 3*barwidth for x in r], list(system.components[0].monthly_state.index), rotation = -90)
plt.tick_params(left=False, labelleft=False) #remove ticks
plt.box(False) #remove box

# %%
