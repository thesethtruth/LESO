## Import relevant packages
import pandas as pd
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, ETMdemand, Grid, FinalBalance, Hydrogen

## Setup the cases to be calculated
scenarios_gelderland = { 
    # '2030Gelderland_hoog': {'id': 815715, 'latlon': (52, 6)},
    # '2030Gelderland_laag': {'id': 815716, 'latlon': (52, 6)},
    '2030RES_Achterhoek': {'id': 815753, 'latlon': (52, 6.4)},
    # '2030RES_ArnhemNijmegen': {'id': 815754, 'latlon': (51.9, 5.9)},
    # '2030RES_Cleantech': {'id': 815755, 'latlon': (52.2, 6.1)},
    # '2030RES_Foodvalley ': {'id': 815756, 'latlon': (52.1, 5.7)},
    # '2030RES_NoordVeluwe': {'id': 815757, 'latlon': (52.4, 5.8)},
    # '2030RES_Rivierenland': {'id': 815758, 'latlon': (51.9, 5.3)},
} 

for modelname, value in scenarios_gelderland.items():
    
    scenario_id = value['id']
    lat, lon = value['latlon']

    # ==========System-setup=======================================================
    system = System(lat, lon, model_name=modelname)
    # =============================================================================
    pva1 =              PhotoVoltaic('PV Full south', dof = True)
    wind1 =             Wind('Onshore turbine', lat=lat, lon=lon, dof = True)
    bat1 =              Lithium('Li-ion EES', dof = True)
    h2 =                Hydrogen('H2 storage', dof = True)
    demand =            ETMdemand('NoordVeluwe2030', scenario_id=scenario_id)
    grid =              Grid('Grid connection', variable_income=2.5e-6)
    deficit =           FinalBalance()
    # =============================================================================

    # Limit grid component capacity as function of maximum demand
    demand.calculate_time_serie()
    peak_demand = -demand.state.power.min()

    grid.installed = 1/3 * peak_demand
    pva1.upper = peak_demand * 4
    wind1.upper = peak_demand * 3
    bat1.upper = peak_demand * 5
    h2.upper = peak_demand * 35

    # add the components to the system
    component_list = [pva1, wind1, bat1, demand, h2, grid, deficit]
    system.add_components(component_list)

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
                unit = 'None'
    )