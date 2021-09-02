from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, Grid, FinalBalance
import os
from experiments_overview import MODEL_FOLDER
import pandas as pd
import matplotlib.pyplot as plt

#%% Define system and components
modelname = "Cablepooling"
lat, lon = 51.81, 5.84  # Nijmegen
equity_share = 0.5 # to bump the roi up to about 7.5%

# initiate System component
system = System(
    lat=lat, 
    lon=lon, 
    model_name=modelname,
    equity_share=equity_share)

# initiate and define components
pv_s = PhotoVoltaic("PV South", azimuth=180, use_ninja=True, dof=True)
pv_e = PhotoVoltaic("PV East", azimuth=90, use_ninja=True, dof=True)
pv_w = PhotoVoltaic("PV West", azimuth=270, use_ninja=True, dof=True)

#%% add the components to the system
# note that we do not add wind now!
component_list = [pv_s, pv_w, pv_e,]
system.add_components(component_list)
system.fetch_input_data()
system.calculate_time_series()
start = 190

for c in system.components:
    print(c.name)
    print(c.state.power.sum())
    c.state.power[start*24:(start+1)*24].plot()


