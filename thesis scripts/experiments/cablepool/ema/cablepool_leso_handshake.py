import os
import uuid
import pyomo.environ as pyo
import numpy as np
from tinydb import TinyDB
from copy import deepcopy as copy

import LESO
from LESO.experiments import ema_pyomo_interface
from LESO.finance import (
    determine_total_investment_cost,
    determine_roi,
    determine_total_net_profit
)

MODEL_FOLDER = os.path.join(os.path.dirname(__file__), "../model")
RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), "../results")
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

RUNID = 210907

MODELS = {
    "brownfield": "cablepool.pkl",
    "greenfield": "cablepool_greenfield.pkl",
}

# ref_system = LESO.System.read_pickle(model_to_open)
METRICS = [
    "PV South installed capacity",
    "PV West installed capacity",
    "PV East installed capacity",
    "2h battery installed capacity",
    "6h battery installed capacity",
    "10h battery installed capacity",
    "Grid connection installed capacity",
]
METRICS.extend(
    [
        "objective_result",
        "total_renewable_energy",
        "total_investment_cost",
        "curtailment",
        "return_on_add_investment",
        "net_profit_add_investment",
    ]
)

OUTPUT_PREFIX = "cablepooling_exp_"

# this is needed due to the dependent but double variant uncertainty ranges given by ATB
def linear_map(value, ):
    min, max = 0.41, 0.70 # @@
    map_min, map_max = 0.42, 0.81 # @@

    frac = (value - min) / (max-min)
    m_value = frac * (map_max-map_min) + map_min

    return m_value

def Handshake(
    pv_cost_factor=None,
    battery_cost_factor=None,
    wind_cost_factor=None,
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
        if isinstance(component, LESO.Wind):
            component.capex = component.capex * wind_cost_factor
        if isinstance(component, LESO.Lithium):
            component.capex_storage = component.capex_storage * battery_cost_factor
            component.capex_power = component.capex_power * linear_map(battery_cost_factor)
    
    # generate file name and filepath for storing
    filename_export = OUTPUT_PREFIX + str(uuid.uuid4().fields[-1])[:10] + ".json"
    filepath = os.path.join(RESULTS_FOLDER, filename_export)

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
    wind_cost_factor=1,
    approach=1,
):
    if approach == 1:
        model =MODELS['brownfield']
        subsidy_scheme = 'brownfield'
        wind_cost_factor = 1 # force wind cost factor to 1 to prevent this from interferirng with brownfield results
    else:
        model = MODELS['greenfield']
        subsidy_scheme = 'greenfield'

    # hand ema_inputs over to the LESO handshake
    system, filename_export = Handshake(
        pv_cost_factor=pv_cost_factor,
        battery_cost_factor=battery_cost_factor,
        wind_cost_factor=wind_cost_factor,
        model=model
    )

    # check for optimalitiy before trying to access all information
    if pyo.check_optimal_termination(system.model.results):

        # extract capacities from system components
        capacities = {
            component.name + " installed capacity": component.installed
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

        # calculate curtailment
        curtailment = sum(sum(
            component.state.power
            for component in system.components
            if isinstance(component, LESO.FinalBalance)
        ))

        # calculate additional investment cost
        total_investment_cost = determine_total_investment_cost(system)
        roi = determine_roi(system)
        net_profit = determine_total_net_profit(system)

        # combine performance indicators to one dictionary
        pi = {
            "objective_result": system.model.results["Problem"][0]["Lower bound"],
            "total_renewable_energy": total_renewable_energy,
            "total_investment_cost": total_investment_cost,
            "curtailment": curtailment,
            "return_on_add_investment": roi,
            "net_profit_add_investment": net_profit,
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
        "subsidy_scheme": subsidy_scheme,
    })
    db_entry.update(meta_data)  # metadata

    # write to db
    db_filename = f"cablepooling_db{RUNID}.json"
    db_path = os.path.join(RESULTS_FOLDER, db_filename)
    with TinyDB(db_path) as db:
        db.insert(db_entry)
    
    return results

