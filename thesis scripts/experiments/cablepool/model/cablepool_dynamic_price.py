#%%
from LESO import System
from LESO import Grid
import pandas as pd
import os

#%% read system definition from regular cable pool
modelname = "cablepool_dynamic"
system = System.read_pickle(os.path.join(os.path.dirname(__file__), "cablepool.pkl"))
system.name = modelname
# extract grid component
for component in system.components:
     if isinstance(component, Grid):
         grid = component

#%% dynamic part
# read .pkl from dynamic_price_analysis
price_filename = "cablepool_dynamic_savgol_filtered_etmprice_31ch4_85co2.pkl"
mwh_prices = pd.read_pickle(os.path.join(os.path.dirname(__file__), price_filename))
energy_market_price = mwh_prices.values / 1e6 # convert from [eu / MWh] to [Meu / MWh]

# set the dynamic pricing to the grid component
grid.variable_income = list(energy_market_price)

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
    filename = modelname.lower()+".pkl"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    system.to_pickle(filepath=filepath)
