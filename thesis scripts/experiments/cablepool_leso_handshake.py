import LESO
from LESO import ema_pyomo_interface
import os
from copy import deepcopy as copy
import uuid
from tinydb import TinyDB
import pyomo.environ as pyo
import numpy as np

from models.experiments_overview import MODEL_FOLDER, RESULT_FOLDER
RUNID = 120821

MODELS = {
    "fixed-fee": "cablepool.pkl",
    "dynamic": "cablepool_dynamic.pkl",
}

# ref_system = LESO.System.read_pickle(model_to_open)
METRICS = [
    "PV Full south installed capactiy",
    "PV West installed capactiy",
    "PV East installed capactiy",
    "Nordex N100/2500 installed capactiy",
    "Li-ion EES installed capactiy",
    "Grid connection installed capactiy",
]
METRICS.extend(
    [
        "objective_result",
        "total_renewable_energy",
        "addtional_investment_cost",
        "curtailment",
    ]
)

OUTPUT_PREFIX = "cablepooling_exp_"


def Handshake(
    pv_cost_factor=None,
    battery_cost_factor=None,
    grid_capacity=None,
    model=None,
):

    # read model based on pricing scheme
    model_to_open = os.path.join(MODEL_FOLDER, model)

    # initiate System component
    system = LESO.System.read_pickle(model_to_open)

    # process ema inputs to components
    for component in system.components:
        if isinstance(component, LESO.PhotoVoltaic):
            component.capex = component.capex * pv_cost_factor
            component.opex = component.opex * pv_cost_factor
        if isinstance(component, LESO.Lithium):
            component.capex = component.capex * battery_cost_factor
            component.opex = component.opex * battery_cost_factor
        if isinstance(component, LESO.Grid):
            component.installed = grid_capacity
    
    # generate file name and filepath for storing
    filename_export = OUTPUT_PREFIX + str(uuid.uuid4().fields[-1])[:6] + ".json"
    filepath = os.path.join(RESULT_FOLDER, filename_export)

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

    return system, filename_export

@ema_pyomo_interface
def CablePooling(
    pv_cost_factor=1,
    battery_cost_factor=1,
    grid_capacity=10,
    pricing_scheme='SDE',
):

    # hand ema_inputs over to the LESO handshake
    system, filename_export = Handshake(
        pv_cost_factor=pv_cost_factor,
        grid_capacity=grid_capacity,
        battery_cost_factor=battery_cost_factor,
        model=MODELS[pricing_scheme]
    )

    # check for optimalitiy before trying to access all information
    if pyo.check_optimal_termination(system.model.results):

        # extract capacities from system components
        capacities = {
            component.name + " installed capactiy": component.installed
            for component in system.components
            if not isinstance(component, LESO.FinalBalance)
        }

        # calculate total renewable energy
        total_renewable_energy = sum(sum(
            component.state.power
            for component in system.components
            if any(
                [isinstance(component, LESO.PhotoVoltaic), isinstance(component, LESO.Wind)]
            )
        ))

        # calculate additional investment cost
        addtional_investment_cost = sum(
            component.installed * component.capex
            for component in system.components
            if any(
                [
                    isinstance(component, LESO.PhotoVoltaic),
                    isinstance(component, LESO.Lithium),
                ]
            )
        )

        # calculate curtailment
        curtailment = sum(sum(
            component.state.power
            for component in system.components
            if isinstance(component, LESO.FinalBalance)
        ))

        # combine performance indicators to one dictionary
        pi = {
            "objective_result": system.model.results["Problem"][0]["Lower bound"],
            "total_renewable_energy": total_renewable_energy,
            "addtional_investment_cost": addtional_investment_cost,
            "curtailment": curtailment,
        }

        # create and update results dictionary
        results = dict()
        results.update(capacities)
        results.update(pi)
        meta_data = {"filename_export": filename_export}
    
    ## Non optimal exit, no results
    else:
        meta_data = {"filename_export": "N/a"}
        results = {metric: np.nan for metric in METRICS}

    ## In any case
    meta_data.update({
        "solving_time": system.model.results["solver"][0]["Time"],
        "solver_status": system.model.results["solver"][0]["status"].__str__(),
        "solver_status_code": system.model.results["solver"][0]["Return code"],
    })

    # create db entry with results, ema_inputs and meta_data
    db_entry = copy(results)    # results
    db_entry.update({           # ema_inputs
        "battery_cost_factor": battery_cost_factor,
        "pv_cost_factor": pv_cost_factor,
        "grid_capacity": grid_capacity,
    })
    db_entry.update(meta_data)  # metadata

    # write to db
    db_path = os.path.join(RESULT_FOLDER, f"cablepooling_db{RUNID}.json")
    with TinyDB(db_path) as db:
        db.insert(db_entry)
    
    return results

