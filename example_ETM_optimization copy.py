## Import relevant packages
from os import name
import pandas as pd
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, ETMdemand, Grid, FinalBalance, PhotoVoltaicAdvanced, WindOffshore


## Define system and components
modelname = 'ETM Noord-Veluwe 1GW 2030'
lat, lon = 52.4, 5.8
system = System(lat, lon, model_name=modelname)
# =============================================================================
pva1 =              PhotoVoltaicAdvanced('PV Full south', dof = True)
pva2 =              PhotoVoltaicAdvanced('PV West', azimuth = 90, dof = True, capex = .55)
pva3 =              PhotoVoltaicAdvanced('PV East', azimuth = -90, dof = True, capex = .55)
pva4 =              PhotoVoltaicAdvanced('trackingPV2-EW', capex = .75,  tracking=True, azimuth=-90, dof = True)
wind1 =             Wind('Onshore turbine', lat=lat, lon=lon, dof = True)
bat1 =              Lithium('Li-ion EES', dof = True)
demand =            ETMdemand('NoordVeluwe2018', scenario_id=815757)
grid =              Grid('Grid connection', installed = 1e9)
deficit =           FinalBalance()
# =============================================================================

# add the components to the system
component_list = [pva1, pva2, pva3, wind1, bat1, demand, deficit, grid]
system.add_components(component_list)

# update upper limit to 2 GW
bound = 2e9
system.update_component_attr('upper', bound)
system.update_component_attr('lower', -bound, overwrite_zero=False)


# system.pyomo_print()

# define the file path and run with optimization with options supplied
filepath = 'cache/'+modelname+'.json'
# system.pyomo_print()

system.optimize(
            objective='tco',        # total cost of ownership
            time=None,              # resorts to default; year 8760h
            store=False,             # write-out to json
            filepath=filepath,          # resorts to default: modelname+timestamp
            solver='gurobi',        # default solver
            nonconvex=False,        # solver option (warning will show if needed)
            solve=True,             # solve or just create model
            unit = 'M'
)