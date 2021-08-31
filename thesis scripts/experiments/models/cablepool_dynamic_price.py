#%%
from LESO import System
from LESO import Grid
import pandas as pd
import os
from experiments_overview import MODEL_FOLDER


#%% read system definition from regular cable pool
modelname = "cablepooling_dynamic"
system = System.read_pickle("cablepool.pkl")
system.name = modelname
# extract grid component
for component in system.components:
     if isinstance(component, Grid):
         grid = component

#%% dynamic part
# read .pkl from dynamic_price_analysis
mwh_prices = pd.read_pickle("cablepool_dynamic_savgol_filtered_etmprice_31ch4_85co2.pkl")
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
    filepath = os.path.join(MODEL_FOLDER, filename)
    system.to_pickle(filepath=filepath)
