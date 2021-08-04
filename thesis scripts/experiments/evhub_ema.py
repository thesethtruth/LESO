# evhub_ema.py

from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid, FinalBalance
import os

#%% Define system and components
modelname = "VREEVHUB_Utrecht_plain"
lat, lon = 52.09, 5.15 # Utrecht
target_dir = "G:\\My Drive\\0 Thesis\\LESO results\\examples"

# initiate System component
system = System(latitude=lat, longitude=lon, model_name=modelname)

# initiate and define components
pv_s = PhotoVoltaic("PV Full south", dof=True)
pv_w = PhotoVoltaic("PV West", azimuth=90, dof=True, capex=0.55) # slightly cheaper (lower land use, straight-forward construction)
pv_e = PhotoVoltaic("PV East", azimuth=-90, dof=True, capex=0.55) # slightly cheaper (lower land use, straight-forward construction)
wind = Wind("Onshore turbine", dof=True)
bat = Lithium("Li-ion EES", dof=True)
charger = FastCharger("DC quickcharger", dof=False)
petrolstation = Consumer("Petrolstation E. demand")
grid = Grid("Grid connection", installed=150e3)
final = FinalBalance(name="curtailment_underload")

#%% add the components to the system

component_list = [pv_s, pv_w, pv_e, wind, bat, charger, petrolstation, final, grid]
system.add_components(component_list)
system.to_pickle("folder=")