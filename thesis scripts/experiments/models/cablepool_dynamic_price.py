#%%
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid, FinalBalance
import os
import pandas as pd
import plotly.graph_objects as go
import csv

#%% Define system and components
modelname = "Cablepooling"
lat, lon = 51.89, 5.86  # Nijmegen 
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

#%% dynamic part

# read csv from ETM and convert into correct unit
with open(os.path.join(os.getcwd(), 'cablepool_price_kea_48ch4_58co2.csv'), newline='') as f:
    reader = csv.reader(f)
    data = list(reader)
    energy_market_price = [float(row[1])/1e6 for row in data[1:]]

# set the dynamic pricing to the grid component
grid.variable_income = energy_market_price

#%% plot the energy price
from scipy.signal import savgol_filter
edf = pd.DataFrame(
    index = pd.date_range(start="01/01/2021", periods=8760, freq='h'),
    data = [price*1e6 for price in energy_market_price],
    columns= ['energy_price']
)
edf['smoother_energy_price'] = savgol_filter(edf.energy_price, 25, 4)


## default
fig = go.Figure(
    data=   go.Scatter(
        x=edf.index,
        y=edf.energy_price.values,
        line_color='#c75252',         
        line_width=1  
    )
)
fig.update_layout(template='simple_white')
fig.update_yaxes(title='Market energy price', tickangle=90, nticks=4, ticksuffix = "€/MWh")
fig.update_xaxes(title="Day of the year", tickformat='%B', nticks=5, tickcolor="rgba(0,0,0,0)")
fig.show()

## Smoother
fig = go.Figure(
    data=   go.Scatter(
        x=edf.index,
        y=edf.smoother_energy_price.values,        
        line_color='#52aec7',       
        line_width=1
    )
)
fig.update_layout(template='simple_white')
fig.update_yaxes(title='Market energy price', nticks=4, ticksuffix = "€/MWh")
fig.update_xaxes(title="Day of the year", tickformat='%B', nticks=5, tickcolor="rgba(0,0,0,0)")
fig.show()


#%% compare

# make a snip
start = 300
duration = 168
snip = edf.iloc[start:start+duration,:].copy()

fig = go.Figure()
# ETM curve
fig.add_trace(
    go.Scatter(
        x=snip.index,
        y=snip.energy_price.values,        
        line_color='grey',       
        line_width=2
    )
)
# smooth curve
fig.add_trace(
    go.Scatter(
        x=snip.index,
        y=snip.smoother_energy_price.values,        
        line_color='#52aec7',       
        line_width=1.5
    )
)

fig.update_layout(template='simple_white')
fig.update_yaxes(title='Market energy price', nticks=4, ticksuffix = "€/MWh")
fig.update_xaxes(title="Day of the year", tickformat='%B', nticks=5, tickcolor="rgba(0,0,0,0)")
fig.show()




#%% add the components to the system
component_list = [pv_s, pv_w, pv_e, wind, bat, final, grid]
system.add_components(component_list)

#%% Pickle the model
from experiments_overview import MODEL_FOLDER
from LESO import System

name = "cablepool_dynamic_price.pkl"
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
