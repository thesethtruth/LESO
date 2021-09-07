from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, Grid, FinalBalance
import os
import pandas as pd
import LESO


battery_cost_factor = 0.41
pv_cost_factor = 0.38


#%% Define system and components
modelname = "cablepool_alternative"
lat, lon = 51.81, 5.84  # Nijmegen
SDE_price = 55
equity_share = 0.3 # cite: ATB, to bump the roi up to about 7.5%
correct_SDE = False
apply_SDE = False
externalize_wind = False

price_filename = "etm_dynamic_savgol_filtered_etmprice_31ch4_85co2.pkl"
price_filepath = os.path.join(os.path.dirname(__file__), price_filename)
retail_prices = pd.read_pickle(price_filepath)
if apply_SDE:
    profile_factor = 0.65 # CE Delft, pag 22-  Scenario’s zon op grote daken
    basis_price = 55 # Arbitrary
    correction_price = lambda retail_prices, profile_factor: retail_prices.mean() * profile_factor
    if correct_SDE:
        SDE_price = basis_price - correction_price(retail_prices, profile_factor)
    retail_prices[retail_prices < SDE_price ] = SDE_price

retail_prices = list((retail_prices/1e6).values) # convert from eu/MWh to M eu/MWh

# initiate System component
system = System(
    lat=lat, 
    lon=lon, 
    model_name=modelname,
    equity_share=equity_share)
system.fetch_input_data()
tmy = system.tmy

# for wind/grid we need to do some preprocessing
wind = Wind(
    "Nordex N100 2500",
    dof=False,
    installed=10,
    turbine_type="Nordex N100 2500",
    hub_height=100,
    use_ninja=True,
)
wind.calculate_time_serie(tmy)
grid_variable_capacity = list((-wind.state.power+10).values)

#%%
grid = Grid("Grid connection", installed=10, variable_cost=999e-6, variable_income=retail_prices)
if externalize_wind:
    grid.variable_capacity = grid_variable_capacity

pv_s = PhotoVoltaic("PV South", azimuth=180, use_ninja=True, dof=True, capex=LESO.defaultvalues.pv['capex']*pv_cost_factor)
pv_e = PhotoVoltaic("PV East", azimuth=90, use_ninja=True, dof=True, capex=LESO.defaultvalues.pv['capex']*pv_cost_factor)
pv_w = PhotoVoltaic("PV West", azimuth=270, use_ninja=True, dof=True, capex=LESO.defaultvalues.pv['capex']*pv_cost_factor)
bat_1h = Lithium(
    "1h battery", 
    dof=True, EP_ratio=1, 
    capex_power=LESO.defaultvalues.lithium['capex_power']*battery_cost_factor,
    capex_storage=LESO.defaultvalues.lithium['capex_storage']*battery_cost_factor
    )
bat_2h = Lithium(
    "2h battery", 
    dof=True, EP_ratio=2, 
    capex_power=LESO.defaultvalues.lithium['capex_power']*battery_cost_factor,
    capex_storage=LESO.defaultvalues.lithium['capex_storage']*battery_cost_factor
    )
bat_6h = Lithium(
    "6h battery", 
    dof=True, EP_ratio=6,
    capex_power=LESO.defaultvalues.lithium['capex_power']*battery_cost_factor,
    capex_storage=LESO.defaultvalues.lithium['capex_storage']*battery_cost_factor
    )
bat_10h = Lithium(
    "10h battery", 
    dof=True, EP_ratio=10,
    capex_power=LESO.defaultvalues.lithium['capex_power']*battery_cost_factor,
    capex_storage=LESO.defaultvalues.lithium['capex_storage']*battery_cost_factor
    )
final = FinalBalance(name="curtailment_underload")

#%% add the components to the system
# note that we do not add wind now!
component_list = [pv_s, pv_w, pv_e, bat_2h, bat_6h, bat_1h, bat_10h, final, grid]
system.add_components(component_list)
if not externalize_wind:
    system.add_components([wind])
#%% Pickle the model

if __name__ == "__main__":
    ## Solve
    if True:
        system.optimize(
                objective='osc',        # overnight system cost
                time=None,              # resorts to default; year 8760h
                store=False,            # write-out to json
                solver='gurobi',        # default solver
                nonconvex=False,        # solver option (warning will show if needed)
                solve=True,             # solve or just create model
        )
    ## Or write to pickle
    elif False: 
        name = modelname.lower()+".pkl"
        filepath = os.path.join(os.path.dirname(__file__), name)
        system.to_pickle(filepath=filepath)