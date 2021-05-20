from os import name
from LESO import System
from LESO import PhotoVoltaic, Wind, Lithium, FastCharger, Consumer, Grid, FinalBalance
import pyomo.environ as pyo


filename = 'VREEVHUB off-grid cheaper battery (50eukWh)'
system = System(52, 5, model_name = filename)
# =============================================================================
pv1 =           PhotoVoltaic('PV Full south', dof = True)
pv2 =           PhotoVoltaic('PV West', azimuth = 90, capex = 0.55, dof = True)
pv3 =           PhotoVoltaic('PV East', azimuth = -90, capex = 0.55, dof = True)
wind1 =         Wind('Windturbine Mikey', dof = True)
wind2 =         Wind('Windturbine Johnson')
bat1 =          Lithium('Li-ion EES', dof = True, capex = 0.05, upper = 10e10)
charger1 =      FastCharger('DC quickcharger')
petrolstation = Consumer('Total petrolstation')
grid =          Grid('Grid connection', installed=0)
dump =          FinalBalance()
# =============================================================================

component_list = [pv1, pv2, pv3, wind1, bat1, charger1, petrolstation, grid, dump]

system.add_components(component_list)


filepath = 'cache/'+filename+'.json'
system.optimize(
            objective='tco',        # total cost of ownership
            time=None,              # resorts to default; year 8760h
            store=True,             # write-out to json
            filepath=filepath,          # resorts to default: modelname+timestamp
            solver='gurobi',        # default solver
            nonconvex=False,        # solver option (warning will show if needed)
            solve=True,             # solve or just create model
)
