from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, Grid, FinalBalance
import os
import pandas as pd
from pathlib import Path
#%%

FOLDER = Path(__file__).parent

#%% Define system and components
modelname = "evhub"
lat, lon = 52.24, 6.19  # Arnhem (A1 westBound naar Apeldoorn na afrit 24 ri afrit 23 thv hmp 105.5)
equity_share = 0.5 # cite: ATB, to bump the roi up to about 7.5%
price_filename = "cablepool_dynamic_savgol_filtered_etmprice_31ch4_85co2.pkl"
retail_prices = list((pd.read_pickle(FOLDER / price_filename)/1e6).values)


# initiate System component
system = System(
    lat=lat, 
    lon=lon, 
    model_name=modelname,
    equity_share=equity_share)

# for wind/grid we need to do some preprocessing


#%%
# initiate and define components
turbine_type = "Nordex N100 2500" # actually Lagerwey L100 2.5 MW, best match
hub_height = 100
wind = Wind(
    "Nordex N100 2500",
    dof=True,
    turbine_type=turbine_type,
    hub_height=hub_height,
    use_ninja=True,)
pv_s = PhotoVoltaic("PV South soundwall", azimuth=180, tilt=70, use_ninja=True, dof=True)
pv_s = PhotoVoltaic("PV South", azimuth=180, use_ninja=True, dof=True)
pv_e = PhotoVoltaic("PV East", azimuth=90, use_ninja=True, dof=True)
pv_w = PhotoVoltaic("PV West", azimuth=270, use_ninja=True, dof=True)
bat_2h = Lithium("2h battery", dof=True, EP_ratio=2)
bat_6h = Lithium("6h battery", dof=True, EP_ratio=6)
grid = Grid("Grid connection", installed=1, variable_cost=retail_prices, variable_income=retail_prices)
final = FinalBalance(name="curtailment_underload")

#%% add the components to the system
component_list = [pv_s, pv_w, pv_e, bat_2h, bat_6h, final, grid]
system.add_components(component_list)
#%% Pickle the model


## Solve
if False:
    system.optimize(
            objective='osc',        # overnight system cost
            time=None,              # resorts to default; year 8760h
            store=False,            # write-out to json
            solver='gurobi',        # default solver
            nonconvex=False,        # solver option (warning will show if needed)
            solve=True,             # solve or just create model
    )
## Or write to pickle
else: 
    name = modelname.lower()+".pkl"
    filepath = FOLDER / name
    system.to_pickle(filepath=filepath)