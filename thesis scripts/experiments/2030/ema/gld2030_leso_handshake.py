import uuid
import pyomo.environ as pyo
import numpy as np
from tinydb import TinyDB
from copy import deepcopy as copy

import LESO
from LESO.experiments import ema_pyomo_interface
from LESO.optimizer.extension import constrain_minimal_share_of_renewables, contexted_constraint
from LESO.finance import (
    determine_total_investment_cost,
    determine_roi,
    determine_total_net_profit,
)

from gld2030_definitions import (
    lithium_storage_linear_map,
    RESULTS_FOLDER,
    MODELS,
    METRICS,
    scenarios_2030,
)

OUTPUT_PREFIX = "gld2030_exp_"
DB_NAMETAG = "gld2030"

def Handshake(
    pv_cost_factor=None,
    wind_cost_factor=None,
    battery_cost_factor=None,
    hydrogen_cost_factor=None,
    scenario=None,
    target_RE_strategy=None,
):
    # initiate System component
    model_to_open = MODELS[scenario]
    system = LESO.System.read_pickle(model_to_open)

    # process ema inputs to components
    for component in system.components:
        if isinstance(component, LESO.PhotoVoltaic):
            component.capex = component.capex * pv_cost_factor
        if isinstance(component, LESO.Wind):
            component.capex = component.capex * wind_cost_factor
        if isinstance(component, LESO.Lithium):
            component.capex_storage = component.capex_storage * battery_cost_factor
            component.capex_power = component.capex_power * lithium_storage_linear_map(
                battery_cost_factor
            )
        if isinstance(component, LESO.Hydrogen):
            component.capex = component.capex * hydrogen_cost_factor
    
        # grab the ETM demand component
        if isinstance(component, LESO.ETMdemand):
            demand = component

    # do something with the target RE strategy
    scenario_data = scenarios_2030[scenario]
    if target_RE_strategy: 
        STRATEGIES = {
            "no_target": (None, None),
            "current_projection_w_export": (scenario_data['target_re_share'], False),
            "current_projection_no_export": (scenario_data['target_re_share_ex_export'], True),
            "fixed_target_60": (.60, True),
            "fixed_target_80": (.80, True),
        }

        target_share, exlude_export = STRATEGIES[target_RE_strategy]



    # generate file name and filepath for storing
    filename_export = OUTPUT_PREFIX + str(uuid.uuid4().fields[-1]) + ".json"
    filepath = RESULTS_FOLDER / filename_export

    if target_share:
        re_share_constraint = contexted_constraint(
            constrain_minimal_share_of_renewables,
            target_share,
            demands=[demand],
            exclude_export_from_share=exlude_export
        )

    ## SOLVE
    system.optimize(
        objective="osc",  # overnight system cost
        additional_constraints= [re_share_constraint],
        time=None,  # resorts to default; year 8760h
        store=True,  # write-out to json
        filepath=filepath,  # resorts to default: modelname+timestamp
        solver="gurobi",  # default solver
        nonconvex=False,  # solver option (warning will show if needed)
        solve=True,  # solve or just create model
    )

    return system, filename_export


@ema_pyomo_interface
def GLD2030(
    pv_cost_factor=1,
    wind_cost_factor=1,
    battery_cost_factor=1,
    hydrogen_cost_factor=1,
    scenario=None,
    target_RE_strategy=None,
    run_ID=None,
):
    
    # hand ema_inputs over to the LESO handshake
    system, filename_export = Handshake(
        pv_cost_factor=pv_cost_factor,
        wind_cost_factor=wind_cost_factor,
        battery_cost_factor=battery_cost_factor,
        hydrogen_cost_factor=hydrogen_cost_factor,
        scenario=scenario,
        target_RE_strategy=target_RE_strategy,
    )

    # check for optimalitiy before trying to access all information
    if pyo.check_optimal_termination(system.model.results):

        # extract capacities from system components
        capacities = {
            component.name + " installed capacity": component.installed
            for component in system.components
            if not isinstance(component, (LESO.FinalBalance, LESO.ETMdemand))
        }

        # calculate total renewable energy
        additional_renewable_energy = sum(
            sum(
                component.state.power
                for component in system.components
                if any(
                    [
                        isinstance(component, LESO.PhotoVoltaic),
                        isinstance(component, LESO.Wind),
                    ]
                )
            )
        )

        # calculate curtailment
        curtailment = sum(
            sum(
                component.state.power
                for component in system.components
                if isinstance(component, LESO.FinalBalance)
            )
        )

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
    meta_data.update(
        {
            "solving_time": system.model.results["solver"][0]["Time"],
            "solver_status": system.model.results["solver"][0]["status"].__str__(),
            "solver_status_code": system.model.results["solver"][0]["Return code"],
        }
    )

    # create db entry with results, ema_inputs and meta_data
    db_entry = copy(results)  # results
    db_entry.update(
        {  # ema_inputs
            "battery_cost_factor": battery_cost_factor,
            "pv_cost_factor": pv_cost_factor,
            "wind_cost_factor": wind_cost_factor,
            "hydrogen_cost_factor": hydrogen_cost_factor,
            "scenario": scenario,
            "target_RE_strategy": target_RE_strategy,
        }
    )
    db_entry.update(meta_data)  # metadata

    # write to db
    db_filename = f"{DB_NAMETAG.stem}_db{run_ID}.json"
    db_path = RESULTS_FOLDER / db_filename
    with TinyDB(db_path) as db:
        db.insert(db_entry)

    return results
