## Import relevant packages
from os import name
import pandas as pd
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, ETMdemand, Grid, FinalBalance, PhotoVoltaicAdvanced, WindOffshore


## Define system and components
modelname = 'ETM Noord-Veluwe 2GW grid Offshore'
lat, lon = 52.4, 5.8
system = System(lat, lon, model_name=modelname)
# =============================================================================
pva1 =              PhotoVoltaicAdvanced('PV Full south', dof = True)
pva2 =              PhotoVoltaicAdvanced('PV West', azimuth = 90, dof = True)
pva3 =              PhotoVoltaicAdvanced('PV East', azimuth = -90, dof = True)
pva4 =              PhotoVoltaicAdvanced('trackingPV2-EW', capex = .75,  tracking=True, azimuth=-90, dof = True)
wind1 =             Wind('Onshore turbine', lat=lat, lon=lon, dof = True)
wind2 =             WindOffshore('OSWF NW', lat=54, lon=5.58, dof = True)
wind3 =             WindOffshore('BWZF2', lat=51.7, lon=3, dof = True)
bat1 =              Lithium('Li-ion EES', dof = True)
demand =            ETMdemand('NoordVeluwe2018')
grid =              Grid('Grid connection', installed = 2e9)
deficit =           FinalBalance()
# =============================================================================

# add the components to the system
component_list = [pva1, pva2, pva3, wind1, wind2, wind3, bat1, demand, deficit, grid]
system.add_components(component_list)

# update upper limit to 2 GW
bound = 2e9
system.update_component_attr('upper', bound)
system.update_component_attr('lower', -bound, overwrite_zero=False)


# system.pyomo_print()

# define the file path and run with optimization with options supplied
filepath = 'cache/'+modelname+'.json'
system.optimize(
            objective='tco',        # total cost of ownership
            time=None,              # resorts to default; year 8760h
            store=True,             # write-out to json
            filepath=filepath,          # resorts to default: modelname+timestamp
            solver='gurobi',        # default solver
            nonconvex=False,        # solver option (warning will show if needed)
            solve=True,             # solve or just create model
            unit = 'M'
)