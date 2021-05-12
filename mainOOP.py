from os import name
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid, FinalBalance



system = System(52, 5, model_name = "VRE-ESS-EV-hub")
# =============================================================================
pv1 =           PhotoVoltaic('PV Full south', dof = True)
pv2 =           PhotoVoltaic('PV West', azimuth = 90, dof = True)
pv3 =           PhotoVoltaic('PV East', azimuth = -90, dof = True)
wind1 =         Wind('Windturbine Mikey', dof = True)
wind2 =         Wind('Windturbine Johnson')
bat1 =          Lithium('Li-ion EES', dof = True)
charger1 =      FastCharger('180 linkerbaan quick-charge 9000')
petrolstation = Consumer('Total petrolstation')
grid =          Grid('210 KVA', installed = 150e3)
# =============================================================================


component_list = [pv1, wind1, bat1, charger1, petrolstation, grid]

system.add_components(component_list)
system.run_merit_order()
system.to_json()