from LESO import components
from pathlib import Path
import uuid
import pyomo.environ as pyo
import numpy as np
from tinydb import TinyDB
from copy import deepcopy as copy

import LESO
from LESO import ema_pyomo_interface
from LESO.finance import (
    determine_total_investment_cost,
    determine_roi,
    determine_total_net_profit
)

MODEL_FOLDER = Path(__file__).parent.parent / "model"
RESULTS_FOLDER = Path(__file__).parent.parent / "results"
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

  
RUNID = 120903

MODEL = MODEL_FOLDER / 'evhub.pkl'

if False: # use this to easily generate the metrics for installed capacity
    ref_system = LESO.System.read_pickle(MODEL)
    m = []
    for c in ref_system.components:
        if not isinstance(c, LESO.FinalBalance):
            out = c.name + " installed capacity"
            m.append(out)

METRICS = [
    'PV South soundwall installed capacity',
    'PV South installed capacity',
    'PV West installed capacity',
    'PV East installed capacity',
    'Nordex N100 2500 installed capacity',
    'Charging demand installed capacity',
    '2h battery installed capacity',
    '6h battery installed capacity',
    '10h battery installed capacity',
    'Grid connection installed capacity'
 ]

METRICS.extend(
    [
        "objective_result",
        "additional_renewable_energy",
        "curtailment",
        "additional_investment_cost",
        "return_on_investment",
        "net_profit",
    ]
)

OUTPUT_PREFIX = "evhub_exp_"

# this is needed due to the dependent but double variant uncertainty ranges given by ATB
def linear_map(value, ):
    min, max = 0.41, 0.70 # @@
    map_min, map_max = 0.42, 0.81 # @@

    frac = (value - min) / (max-min)
    m_value = frac * (map_max-map_min) + map_min

    return m_value

def Handshake(
    pv_cost_factor=None,
    wind_cost_factor=None,
    battery_cost_factor=None,
    grid_capacity=None,
    model_to_open=MODEL,
):

    # initiate System component
    system = LESO.System.read_pickle(model_to_open)

    # process ema inputs to components
    for component in system.components:
        if isinstance(component, LESO.PhotoVoltaic):
            component.capex = component.capex * pv_cost_factor
        if isinstance(component, LESO.Lithium):
            component.capex_storage = component.capex_storage * battery_cost_factor
            component.capex_power = component.capex_power * linear_map(battery_cost_factor)
        if isinstance(component, LESO.Wind):
            component.capex = component.capex * wind_cost_factor
        if isinstance(component, LESO.Grid):
            component.installed = grid_capacity
    
    # generate file name and filepath for storing
    filename_export = OUTPUT_PREFIX + str(uuid.uuid4().fields[-1])[:6] + ".json"
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

    return system, filename_export

@ema_pyomo_interface
def EVHub(
    pv_cost_factor=1,
    battery_cost_factor=1,
    wind_cost_factor=1,
    grid_capacity=1,
):

    # hand ema_inputs over to the LESO handshake
    system, filename_export = Handshake(
        pv_cost_factor=pv_cost_factor,
        wind_cost_factor=wind_cost_factor,
        battery_cost_factor=battery_cost_factor,
        grid_capacity=grid_capacity,
        model_to_open=MODEL,
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
        additional_renewable_energy = sum(sum(
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
        addtional_investment_cost = determine_total_investment_cost(system)
        roi = determine_roi(system)
        net_profit = determine_total_net_profit(system)

        # combine performance indicators to one dictionary
        pi = {
            "objective_result": system.model.results["Problem"][0]["Lower bound"],
            "additional_renewable_energy": additional_renewable_energy,
            "curtailment": curtailment,
            "return_on_investment": roi,
            "net_profit": net_profit,
            "additional_investment_cost": addtional_investment_cost,
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
        "wind_cost_factor": wind_cost_factor,
        "grid_capacity": grid_capacity,
    })
    db_entry.update(meta_data)  # metadata

    # write to db
    db_filename = f"{MODEL.stem}_db{RUNID}.json"
    db_path = RESULTS_FOLDER / db_filename
    with TinyDB(db_path) as db:
        db.insert(db_entry)
    
    return results

