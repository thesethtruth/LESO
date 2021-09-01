from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, Grid, FinalBalance
import os
from experiments_overview import MODEL_FOLDER
import pandas as pd

#%% Define system and components
modelname = "Cablepooling"
lat, lon = 51.81, 5.84  # Nijmegen
SDE_price = 55 # TODO
retail_prices = pd.read_pickle("cablepool_dynamic_savgol_filtered_etmprice_31ch4_85co2.pkl")

if True:
    profile_factor = 0.65 # CE Delft, pag 22-  Scenario’s zon op grote daken
    basis_price = 55 # Arbitrary
    retail_prices = pd.read_pickle("cablepool_dynamic_savgol_filtered_etmprice_31ch4_85co2.pkl")
    correction_price = lambda retail_prices, profile_factor: retail_prices.mean() * profile_factor
    SDE_price = basis_price - correction_price(retail_prices, profile_factor)

retail_prices[retail_prices < SDE_price ] = SDE_price
retail_prices = list((retail_prices/1e6).values) # convert from eu/MWh to M eu/MWh

# initiate System component
system = System(lat=lat, lon=lon, model_name=modelname)
system.fetch_input_data()
tmy = system.tmy

# for wind/grid we need to do some preprocessing
turbine_type = "Nordex N100 2500" # actually Lagerwey L100 2.5 MW, best match
hub_height = 100
wind = Wind(
    "Nordex N100 2500",
    dof=False,
    installed=10,
    turbine_type=turbine_type,
    hub_height=hub_height,
    use_ninja=True,
)
wind.calculate_time_serie(tmy)
grid_variable_capacity = list((-wind.state.power+10).values)

#%%
grid = Grid("Grid connection", installed=10, variable_cost=999e-6, variable_income=retail_prices)
grid.variable_capacity = grid_variable_capacity

# initiate and define components
pv_s = PhotoVoltaic("PV South", azimuth=180, use_ninja=True, dof=True)
pv_e = PhotoVoltaic("PV East", azimuth=90, use_ninja=True, dof=True)
pv_w = PhotoVoltaic("PV West", azimuth=270, use_ninja=True, dof=True)
bat_2h = Lithium("2h battery", dof=True, EP_ratio=2)
bat_6h = Lithium("6h battery", dof=True, EP_ratio=6)
final = FinalBalance(name="curtailment_underload")

#%% add the components to the system
# note that we do not add wind now!
component_list = [pv_s, pv_w, pv_e, bat_2h, bat_6h, final, grid]
system.add_components(component_list)
#%% Pickle the model


## Solve
if True:
    system.optimize(
            objective='profit',        # overnight system cost
            time=None,              # resorts to default; year 8760h
            store=False,             # write-out to json
            solver='gurobi',        # default solver
            nonconvex=False,        # solver option (warning will show if needed)
            solve=True,             # solve or just create model
    )
## Or write to pickle
else: 
    name = "cablepool.pkl"
    filepath = os.path.join(MODEL_FOLDER, name)
    system.to_pickle(filepath=filepath)
