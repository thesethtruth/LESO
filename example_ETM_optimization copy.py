## Import relevant packages
from os import name
import pandas as pd
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, ETMdemand, Grid, FinalBalance, PhotoVoltaicAdvanced, WindOffshore, Hydrogen


## Define system and components
modelname = 'ETM Noord-Veluwe 2030 latest trial'
lat, lon = 52.4, 5.8
system = System(lat, lon, model_name=modelname)
# =============================================================================
pva1 =              PhotoVoltaicAdvanced('PV Full south', dof = True)
pva2 =              PhotoVoltaicAdvanced('PV West', azimuth = 90, dof = True, capex = .55)
pva3 =              PhotoVoltaicAdvanced('PV East', azimuth = -90, dof = True, capex = .55)
pva4 =              PhotoVoltaicAdvanced('trackingPV2-EW', capex = .75,  tracking=True, azimuth=-90, dof = True)
wind1 =             Wind('Onshore turbine', lat=lat, lon=lon, dof = True)
bat1 =              Lithium('Li-ion EES', dof = True)
h2 =                Hydrogen('H2 storage', dof = True, capex= 1200e-3)
demand =            ETMdemand('NoordVeluwe2030', scenario_id=815757)
grid =              Grid('Grid connection', installed = 50e6, variable_income=2.5e-6)
deficit =           FinalBalance()
# =============================================================================

# add the components to the system
component_list = [pva1, wind1, bat1, demand, h2, grid, deficit]
system.add_components(component_list)

# update upper limit to 2 GW
bound = 500e6
system.update_component_attr('upper', bound)
system.update_component_attr('lower', -bound, overwrite_zero=False)
h2.upper = 10e9

# system.pyomo_print()

# define the file path and run with optimization with options supplied
filepath = 'cache/'+modelname+'.json'
# system.pyomo_print()

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