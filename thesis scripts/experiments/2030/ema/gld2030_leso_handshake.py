import uuid
import pyomo.environ as pyo
import numpy as np
from copy import deepcopy as copy
from LESO.experiments.analysis import (
    gdatastore_put_entry,
    gcloud_upload_experiment_dict,
)

import LESO
from LESO.experiments import ema_pyomo_interface
from LESO.optimizer.extension import constrain_minimal_share_of_renewables, contexted_constraint
from LESO.finance import (
    determine_total_investment_cost,
    determine_roi,
    determine_total_net_profit,
)
from LESO.leso_logging import get_module_logger
logger = get_module_logger(__name__)

from gld2030_definitions import (
    COLLECTION,
    MODELS,
    OUTPUT_PREFIX,
    linear_map_2030,
    RESULTS_FOLDER,
    METRICS,    
    scenarios_2030,
)

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
            component.capex_power = component.capex_power * linear_map_2030(
                battery_cost_factor
            )
        if isinstance(component, LESO.Hydrogen):
            component.capex_power = component.capex_power * hydrogen_cost_factor
            component.capex_storage = component.capex_storage * hydrogen_cost_factor
    
        # grab the ETM demand component
        if isinstance(component, LESO.ETMdemand):
            demand = component

    # do something with the target RE strategy
    scenario_data = scenarios_2030[scenario]
    if target_RE_strategy: 
        STRATEGIES = {
            "no_target": (None, None),
            "current_projection_include_export": (scenario_data['target_re_share'], False),
            "current_projection_excl_export": (scenario_data['target_re_share_ex_export'], True),
            "fixed_target_60": (.60, True),
            "fixed_target_80": (.80, True),
            "fixed_target_100": (1, True),
        }

        target_share, exlude_export = STRATEGIES[target_RE_strategy]



    # generate file name and filepath for storing
    filename_export = OUTPUT_PREFIX + str(uuid.uuid4().fields[-1]) + ".json"
    filepath = RESULTS_FOLDER / filename_export
    logfile = filename_export.replace(".json", ".log")

    # set the correct context and share
    if target_share:
        re_share_constraint = contexted_constraint(
            constrain_minimal_share_of_renewables,
            share_of_re=target_share,
            demands=[demand],
            exclude_export_from_share=exlude_export
        )
    else: 
        re_share_constraint = None

    ## initiate the solver kwargs
    solver_kwrgs = {
        "BarConvTol": 1e-5,
        "LogToConsole": 0,
        "LogFile": logfile,
        "Method": 2,
        "Crossover": 0
        }
    ## SOLVE
    system.optimize(
        objective="osc",  # overnight system cost
        additional_constraints= re_share_constraint,
        time=None,  # resorts to default; year 8760h
        store=True,  # write-out to json
        filepath=filepath,  # resorts to default: modelname+timestamp
        solver="gurobi",  # default solver
        nonconvex=False,  # solver option (warning will show if needed)
        solve=True,  # solve or just create model
        tee=True,
        solver_kwrgs=solver_kwrgs
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
    
    # compute the total storage reflux, only exists when optimisation is succesful (therefore hassattr)
    total_reflux = 0
    for component in system.components:
        if isinstance(component, LESO.Storage) and hasattr(component, "reflux"):
            total_reflux += component.reflux
    solving_time = system.model.results["solver"][0]["Time"]
    if solving_time > 500:
        logger.warn(f"solving took a long time: {int(solving_time)} s")
    else:
        logger.info(f"gurobi found the optimum in: {int(solving_time)} s")
    ## In any case
    meta_data.update(
        {
            "solving_time": solving_time,
            "solver_status": system.model.results["solver"][0]["status"].__str__(),
            "solver_status_code": system.model.results["solver"][0]["Return code"],
            "battery_reflux": total_reflux
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
    db_entry.update({"run_id": run_ID})

    # put db_entry to google datastore, keeps retrying when internet is down.
    succesful = False
    while not succesful:
        try:
            gdatastore_put_entry(COLLECTION, db_entry)
            succesful = True
        except:
            pass

    # put system.results to google cloud, keeps retrying when internet is down.
    succesful = False
    while not succesful:
        try:
            gcloud_upload_experiment_dict(system.results, COLLECTION, filename_export)
            succesful = True
        except:
            pass

    return results
