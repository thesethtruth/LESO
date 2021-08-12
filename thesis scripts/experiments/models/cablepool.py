from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid, FinalBalance
import os

#%% Define system and components
modelname = "Cablepooling"
lat, lon = 51.81, 5.84  # Nijmegen

# initiate System component
system = System(latitude=lat, longitude=lon, model_name=modelname)

# initiate and define components
turbine_type = "N100/2500" # actually Lagerwey L100 2.5 MW, best match
hub_height = 100
wind = Wind(
    "Nordex N100/2500",
    dof=False,
    installed=10,
    turbine_type=turbine_type,
    hub_height=hub_height,
)

pv_s = PhotoVoltaic("PV Full south", dof=True)
pv_w = PhotoVoltaic("PV West", azimuth=90, dof=True, capex=0.55)
pv_e = PhotoVoltaic("PV East", azimuth=-90, dof=True, capex=0.55)
bat = Lithium("Li-ion EES", dof=True)
grid = Grid("Grid connection", installed=10, variable_cost=999e-6, variable_income=100e-6)
final = FinalBalance(name="curtailment_underload")

#%% add the components to the system
component_list = [pv_s, pv_w, pv_e, wind, bat, final, grid]
system.add_components(component_list)


#%% Pickle the model
from experiments_overview import MODEL_FOLDER
from LESO import System

name = "cablepool.pkl"
filepath = os.path.join(MODEL_FOLDER, name)

## Solve
if False:
    system.optimize(
            objective='osc',        # overnight system cost
            time=None,              # resorts to default; year 8760h
            store=False,             # write-out to json
            solver='gurobi',        # default solver
            nonconvex=False,        # solver option (warning will show if needed)
            solve=True,             # solve or just create model
    )
## Or write to pickle
else: 
    system.to_pickle(filepath=filepath)
