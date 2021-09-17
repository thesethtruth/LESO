#%%
from LESO.components import ETMdemand
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, Grid, FinalBalance
from LESO.defaultvalues import scenarios_gelderland

modelname = "cablepool"
lat, lon = 51.81, 5.84  # Nijmegen

# initiate System component
system = System(
    lat=lat, 
    lon=lon, 
    model_name=modelname,
    equity_share=0.2)

#%% 
grid = Grid("Grid connection", installed=10)
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
demand = ETMdemand("Noord-Veluwe", scenario_id=815757, end_year=2030, dof=False)
final = FinalBalance(name="curtailment_underload")

#%% add the components to the system
# note that we do not add wind now!
component_list = [pv_s, wind, pv_w, pv_e, bat_2h, bat_6h, bat_10h, demand, final, grid]
system.add_components(component_list)
#%% Pickle the model
system.fetch_input_data()
system.calculate_time_series()

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


#%%
with open("etm_curves.txt", "r") as file:
    lines = file.readlines()
    file.close()
    lines = [line.strip() for line in lines]

input_flex = []
output_flex = []
for i, line in enumerate(lines):
    if 'flex' in line:
        if 'input' in line:
            input_flex.append(line)
        elif 'output' in line:
            output_flex.append(line)
        else:
            print(line)

        lines.pop(i)
    
remaining_inputs = [line for line in lines if 'input' in line]
remaining_outputs = [line for line in lines if 'output' in line]
white_listed = [line for line in remaining_outputs if not ('solar' in line or 'wind' in line)]
# %%
from LESO import Hydrogen

hy = Hydrogen("test")