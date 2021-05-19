from os import name
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid, FinalBalance
import pyomo.environ as pyo


system = System(52, 5, model_name = "VRE-ESS-EV-hub")
# =============================================================================
pv1 =           PhotoVoltaic('PV Full south', dof = True)
pv2 =           PhotoVoltaic('PV West', azimuth = 90, capex = 0.55, dof = True)
pv3 =           PhotoVoltaic('PV East', azimuth = -90, capex = 0.55, dof = True)
wind1 =         Wind('Windturbine Mikey', dof = True)
wind2 =         Wind('Windturbine Johnson')
bat1 =          Lithium('Li-ion EES', dof = True)
charger1 =      FastCharger('180 linkerbaan quick-charge 9000', dof = False)
petrolstation = Consumer('Total petrolstation')
grid =          Grid('210 KVA', installed = 100e3)
dump =          FinalBalance()
# =============================================================================

component_list = [pv1, pv2, pv3, wind1, bat1, charger1, petrolstation, grid, dump]

system.add_components(component_list)
system.optimize(
            objective='tco',        # total cost of ownership
            time=None,              # resorts to default; year 8760h
            store=True,             # write-out to json
            filepath=None,          # resorts to default: modelname+timestamp
            solver='gurobi',        # default solver
            nonconvex=False,        # solver option (warning will show if needed)
            solve=True,             # solve or just create model
)

# system.pyomo_print()