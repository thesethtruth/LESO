from LESO import System
from LESO.components import PhotoVoltaic, Wind, Lithium, Grid, FinalBalance, Hydrogen, ETMdemand
import pandas as pd
from pathlib import Path
from gld2050_definitions import scenarios_2050


#%%
FOLDER = Path(__file__).parent

# parameters used:
equity_share = 0.2 # no cite
end_year = 2050

#%% Define system and components

# this will define 4 models
for modelname, scenario in scenarios_2050.items():

    ## apply default price
    scenario_id = scenario['id']
    lat, lon = scenario['latlon']
    etm_grid_capacity = scenario['grid_cap']
    price_filename = scenario["price_curve"]
    retail_prices = list((pd.read_pickle(FOLDER / price_filename)/1e6).values)

    # initiate System component
    system = System(
        lat=lat, 
        lon=lon, 
        model_name=modelname,
        equity_share=equity_share)

    #%% initiate and define components

    # demand
    from LESO.defaultvalues import generation_whitelist
    demand = ETMdemand(
        "ETM residual load",
        scenario_id,
        end_year=end_year,
        generation_whitelist=generation_whitelist,
    )

    # wind
    wind = Wind(
        "Vestas V90 2000",
        dof=True,
        turbine_type="Vestas V90 2000" ,
        hub_height=80,
        use_ninja=True,
    )

    # solar
    pv_s = PhotoVoltaic("PV South", azimuth=180, use_ninja=True, dof=True)
    pv_e = PhotoVoltaic("PV East", azimuth=90, use_ninja=True, dof=True)
    pv_w = PhotoVoltaic("PV West", azimuth=270, use_ninja=True, dof=True)

    # storage
    bat_2h = Lithium("2h battery", dof=True, EP_ratio=2)
    bat_6h = Lithium("6h battery", dof=True, EP_ratio=6)
    bat_10h = Lithium("10h battery", dof=True, EP_ratio=10)
    h2_seasonal = Hydrogen("H2 seasonal", dof=True, EP_ratio=700)
    h2_subseasonal = Hydrogen("H2 subseasonal", dof=True, EP_ratio=350)

    # grid and curtailment
    grid = Grid(
        "Grid connection", 
        installed=etm_grid_capacity, 
        variable_cost=retail_prices, 
        variable_income=retail_prices
    )
    final = FinalBalance(name="Curtailment")

    #%% add the components to the system
    component_list = [demand, pv_s, pv_w, pv_e, wind, bat_2h, bat_6h, bat_10h, h2_seasonal, h2_subseasonal, final, grid]
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