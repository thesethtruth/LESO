from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid



# model = System(52, 5, model_name = "VRE-ESS-EV-hub")
# # =============================================================================

# pv1 =           PhotoVoltaic('PV Full south')
# pv2 =           PhotoVoltaic('PV West', azimuth = 90)
# pv3 =           PhotoVoltaic('PV East', azimuth = -90)
# wind1 =         Wind('Windturbine Mikey')
# wind2 =         Wind('Windturbine   Johnson')
# bat1 =          Lithium('Li-ion EES')
# charger1 =      FastCharger('180 linkerbaan quick-charge 9000')
# petrolstation = Consumer('Total petrolstation')
# grid =          Grid('210 KVA', installed = 210e3)
# # =============================================================================


# component_list = [pv1, wind1, bat1, charger1, petrolstation, grid]

# model.add_components(component_list)

# model.run_merit_order()
  
# model.balance

system = System.from_pickle('LESO model')

components = system.components