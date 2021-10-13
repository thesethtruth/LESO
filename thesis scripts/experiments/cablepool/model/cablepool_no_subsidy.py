#%%
from LESO import System
from LESO import Grid, Wind
import pandas as pd
from pathlib import Path

FOLDER = Path(__file__).parent

#%% read system definition from regular cable pool
modelname = "cablepool_no_subsidy"
system = System.read_pickle(FOLDER / "cablepool.pkl")
system.name = modelname
# grab grid component
for component in system.components:
     if isinstance(component, Grid):
         grid = component

#%% dynamic part
# read .pkl from dynamic_price_analysis
price_filename = "etm_dynamic_savgol_filtered_etmprice_40ch4_85co2.pkl"
mwh_prices = pd.read_pickle(FOLDER / price_filename)
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
    system.to_pickle(FOLDER / filename)