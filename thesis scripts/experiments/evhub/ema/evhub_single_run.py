#%%
import uuid
import LESO
from LESO.leso_logging import log_to_stderr, INFO
from LESO.experiments.analysis import gdatastore_results_to_df


from evhub_definitions import (
    COLLECTION,
    MODEL,
    OUTPUT_PREFIX,
    linear_map_2030,
    RESULTS_FOLDER,
    METRICS,
)

log_to_stderr(level=INFO)

model_to_open = MODEL
grid_capacity = 1.0

#%%
COLLECTION = "evhub"
RUN_ID = "2210_v2"

filter = ("run_id", "=", RUN_ID)
db = gdatastore_results_to_df(
    collection=COLLECTION,
    filter=filter
)

#%%
dbc = db.copy(deep=True)
dbc.sort_values('solving_time', ascending=False, inplace=True)
for exp_to_select in range(2,6):
    exp = dbc.iloc[exp_to_select,:]

    grid_capacity = float(exp.grid_capacity)
    pv_cost_factor = float(exp.pv_cost_factor)
    battery_cost_factor = float(exp.battery_cost_factor)
    wind_cost_factor = float(exp.wind_cost_factor)


    #%%
    # initiate System component
    system = LESO.System.read_pickle(model_to_open)

    # process ema inputs to components
    for component in system.components:
        if isinstance(component, LESO.PhotoVoltaic):
            component.capex = component.capex * pv_cost_factor
        if isinstance(component, LESO.Lithium):
            component.capex_storage = component.capex_storage * battery_cost_factor
            component.capex_power = component.capex_power * linear_map_2030(
                battery_cost_factor
            )
        if isinstance(component, LESO.Wind):
            component.capex = component.capex * wind_cost_factor
        if isinstance(component, LESO.Grid):
            component.installed = grid_capacity

    # generate file name and filepath for storing
    filename_export = OUTPUT_PREFIX + str(uuid.uuid4().fields[-1]) + ".json"
    filepath = RESULTS_FOLDER / filename_export

    ## SOLVE
    system.optimize(
        objective="osc",  # overnight system cost
        store=True,  # write-out to json
        filepath=filepath,  # resorts to default: modelname+timestamp
        solver="gurobi",  # default solver
        solve=True,  # solve or just create model
        # tee=True,
        solver_kwrgs ={
            "BarConvTol": 1e-12
        }
    )

    # %%
    solving_time = system.model.results["solver"][0]["Time"]
    settings = {
        grid_capacity: "grid_capacity", 
        pv_cost_factor: "pv_cost_factor",
        battery_cost_factor: "battery_cost_factor",
        wind_cost_factor: "wind_cost_factor",
    }
    print("============================================")
    print(exp.filename_export)
    for value, key in settings.items():
        print(f"\t{key:<20}{round(value,3):>15}" )
    print("============================================")
    print(f"BEFORE: selected experiment was solved in:\n {int(exp.solving_time):>40} s")
    print(f"NOW: selected experiment was solved in:\n {int(solving_time):>40} s")