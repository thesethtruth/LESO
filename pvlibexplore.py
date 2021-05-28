# pvlibexplore.py

import pvlib
from LESO.feedinfunctions import PVweather
cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')

huawei = list()
for col in cec_inverters.columns:
    if 'Hua' in col:
        huawei.append(col)

jinko = list()
for col in cec_modules.columns:
    if 'Jinko' in col:
        jinko.append(col)

jinko_example = cec_modules['Jinko_Solar_Co___Ltd_JKM350M_72_V']

from LESO import System
from LESO import PhotoVoltaic, PhotoVoltaicAdvanced

pv1 =           PhotoVoltaic('simplePV')
pv2 =           PhotoVoltaicAdvanced('pvlibPV')
pv3 =           PhotoVoltaicAdvanced('trackingPV', tracking=True)
pv4 =           PhotoVoltaicAdvanced('trackingPV2', tracking=True, azimuth=-90)

filename = 'Trial to compare'
system = System(52, 5, model_name = filename)
system.add_components([pv1, pv2, pv3, pv4])
system.fetch_input_data()
system.calculate_time_series()

print(pv1.state.power.sum()/pv1.installed)
print(pv2.state.power.sum()/pv2.installed)
print(pv3.state.power.sum()/pv3.installed)
print(pv4.state.power.sum()/pv4.installed)