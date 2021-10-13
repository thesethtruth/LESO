# cablepool_singlerun.py
import LESO
from cablepool_definitions import (
    linear_map_2030,
    linear_map_2050,
    RESULTS_FOLDER,
    MODELS,
    METRICS,
)
import uuid

APPROACH = approach = "no_subsidy"
model = MODELS[approach]
pv_cost_factor = 0.38
battery_cost_factor = 0.41
OUTPUT_PREFIX = "cablepooling_exp_"
DB_NAMETAG = COLLECTION = "cablepooling"

# initiate System component
system = LESO.System.read_pickle(model)


if approach == "cheap_battery":
    linear_map = linear_map_2050
else:
    linear_map = linear_map_2030

# process ema inputs to components
for component in system.components:
    if isinstance(component, LESO.PhotoVoltaic):
        component.capex = component.capex * pv_cost_factor
    if isinstance(component, LESO.Lithium):
        component.capex_storage = component.capex_storage * battery_cost_factor
        component.capex_power = component.capex_power * linear_map(battery_cost_factor)

# generate file name and filepath for storing
filename_export = OUTPUT_PREFIX + str(uuid.uuid4().fields[-1]) + ".json"
filepath = RESULTS_FOLDER / filename_export

## SOLVE
system.optimize(
    objective="osc",  # overnight system cost
    time=None,  # resorts to default; year 8760h
    store=True,  # write-out to json
    filepath=filepath,  # resorts to default: modelname+timestamp
    solver="gurobi",  # default solver
    nonconvex=False,  # solver option (warning will show if needed)
    solve=True,  # solve or just create model
)
