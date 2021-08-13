import LESO
import os
from copy import deepcopy as copy
import uuid
import numpy as np
from numpy import float64
from tinydb import TinyDB

from models.experiments_overview import MODEL_FOLDER, RESULT_FOLDER
RUNID = 120821

MODEL_NAME = "evhub.pkl"
model_to_open = os.path.join(MODEL_FOLDER, MODEL_NAME)

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

OUTPUT_PREFIX = "evhub_exp_"


def Handshake(
    pv_cost_factor=None,
    battery_cost_factor=None,
    grid_capacity=None
):

    # initiate System component
    system = LESO.System.read_pickle(model_to_open)

    for component in system.components:

        if isinstance(component, LESO.PhotoVoltaic):
            component.capex = component.capex * float(pv_cost_factor)
            component.opex = component.capex * float(pv_cost_factor)
        if isinstance(component, LESO.Lithium):
            component.capex = component.capex * float(battery_cost_factor)
            component.capex = component.capex * float(battery_cost_factor)
        if isinstance(component, LESO.Grid):
            component.installed = grid_capacity
    
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


def CablePooling(
    pv_cost_factor=1,
    battery_cost_factor=1,
    grid_capacity=10
):

    system, filename_export = Handshake(
        pv_cost_factor=pv_cost_factor,
        grid_capacity=grid_capacity,
        battery_cost_factor=battery_cost_factor,
    )

    ## Extract data
    capacities = {
        component.name + " installed capactiy": component.installed
        for component in system.components
        if not isinstance(component, LESO.FinalBalance)
    }

    total_renewable_energy = sum(sum(
        component.state.power
        for component in system.components
        if any(
            [isinstance(component, LESO.PhotoVoltaic), isinstance(component, LESO.Wind)]
        )
    ))
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
    curtailment = sum(sum(
        component.state.power
        for component in system.components
        if isinstance(component, LESO.FinalBalance)
    ))

    pi = {
        "objective_result": system.model.results["Problem"][0]["Lower bound"],
        "total_renewable_energy": total_renewable_energy,
        "addtional_investment_cost": addtional_investment_cost,
        "curtailment": curtailment,
    }

    meta_data = {
        "solving_time": system.model.results["solver"][0]["Time"],
        "solver_status": system.model.results["solver"][0]["status"].__str__(),
        "solver_status_code": system.model.results["solver"][0]["Return code"],
        "filename_export": filename_export,
    }

    results = dict()
    results.update(capacities)
    results.update(pi)

    ## db for browsing
    db_entry = copy(results)
    db_entry.update(meta_data)
    db_entry.update({
        "battery_cost_factor": battery_cost_factor,
        "pv_cost_factor": pv_cost_factor,
        "grid_capacity": grid_capacity,
    })

    db_path = os.path.join(RESULT_FOLDER, f"cablepooling_db{RUNID}.json")
    with TinyDB(db_path) as db:
        db.insert(db_entry)
    
    ## force to float64 for further processing
    results = {key: float64(value) for key, value in results.items()}
    
    return results

