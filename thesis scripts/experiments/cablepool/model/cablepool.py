#%%
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, Grid, FinalBalance
import pandas as pd
from pathlib import Path

FOLDER = Path(__file__).parent
model_options= {
    "cablepool_subsidy" : True,
    "cablepool_no_subsidy": False,
}

for modelname, apply_subsidy in model_options.items():
    #%% Define system and components
    modelname = modelname
    lat, lon = 51.81, 5.84  # Nijmegen
    SDE_price = 55 # TODO
    equity_share = 0.5 # cite: ATB, to bump the roi up to about 7.5%
    correct_SDE = True

    price_filename = "etm_dynamic_savgol_filtered_etmprice_40ch4_85co2.pkl"
    retail_prices = pd.read_pickle(FOLDER / price_filename)

    if apply_subsidy:
        profile_factor = 0.65 # CE Delft, pag 22-  Scenario’s zon op grote daken
        basis_price = 55 # Arbitrary, loosely based on projected SDE for 2022
        correction_price = lambda retail_prices, profile_factor: retail_prices.mean() * profile_factor
        SDE_price = basis_price - correction_price(retail_prices, profile_factor)
        retail_prices[retail_prices < SDE_price ] = SDE_price

    retail_prices = list((retail_prices/1e6).values) # convert from eu/MWh to M eu/MWh

    # initiate System component
    system = System(
        lat=lat, 
        lon=lon, 
        model_name=modelname,
        equity_share=equity_share)

    #%% 
    grid = Grid("Grid connection", installed=10, variable_cost=999e-6, variable_income=retail_prices)
    wind = Wind(
        "Nordex N100 2500",
        dof=False,
        installed=10,
        turbine_type="Nordex N100 2500", # actually Lagerwey L100 2.5 MW, best match
        hub_height=100,
        use_ninja=True,
    )
    pv_s = PhotoVoltaic("PV South", azimuth=180, use_ninja=True, dof=True)
    pv_e = PhotoVoltaic("PV East", azimuth=90, use_ninja=True, dof=True)
    pv_w = PhotoVoltaic("PV West", azimuth=270, use_ninja=True, dof=True)
    bat_2h = Lithium("2h battery", dof=True, EP_ratio=2)
    bat_6h = Lithium("6h battery", dof=True, EP_ratio=6)
    bat_10h = Lithium("10h battery", dof=True, EP_ratio=10)
    final = FinalBalance(name="curtailment_underload")

    #%% add the components to the system
    # note that we do not add wind now!
    component_list = [pv_s, wind, pv_w, pv_e, bat_2h, bat_6h, bat_10h, final, grid]
    system.add_components(component_list)
    #%% Pickle the model

    if __name__ == "__main__":
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
            filename = modelname.lower()+".pkl"
            system.to_pickle(FOLDER / filename)