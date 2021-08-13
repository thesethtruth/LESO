from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid, FinalBalance
import os

#%% Define system and components
modelname = "VREEVHUB_Utrecht_plain"
lat, lon = 52.09, 5.15  # Utrecht

# initiate System component
system = System(latitude=lat, longitude=lon, model_name=modelname)

# initiate and define components
turbine_type = "N100/2500"
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
charger = FastCharger("DC quickcharger", dof=False)
petrolstation = Consumer("Petrolstation E. demand", scaler=40) #40MWh per year
grid = Grid("Grid connection", installed=250e3)
final = FinalBalance(name="curtailment_underload")

#%% add the components to the system
component_list = [pv_s, pv_w, pv_e, wind, bat, charger, petrolstation, final, grid]
system.add_components(component_list)

#%% Pickle the model
from experiments_overview import MODEL_FOLDER

name = "evhub.pkl"
filepath = os.path.join(MODEL_FOLDER, name)
system.to_pickle(filepath=filepath)