#%%
from functools import partial
from ema_workbench import (
    perform_experiments,
    save_results,
    RealParameter,
    CategoricalParameter,
    ScalarOutcome,
    Constant,
    Model,
    ema_logging,
    MultiprocessingEvaluator,
    SequentialEvaluator,
)
from gld2030_leso_handshake import GLD2030
from gld2030_definitions import (
    RES_SCENARIOS,
    COLLECTION,
    RESULTS_FOLDER,
    METRICS,
    PV_COST_CENTER_FACTOR,
    WIND_COST_CENTER_FACTOR,
    HYDROGEN_COST_CENTER_FACTOR,
    BATTERY_COST_CENTER_FACTOR,
)

#%%
if __name__ == "__main__":

    ema_logging.log_to_stderr(ema_logging.INFO)

    # initiate model
    run_ID = input("Please enter the run ID:")
    initialized_model = partial(
        GLD2030,
        run_ID=run_ID,
        pv_cost_factor=PV_COST_CENTER_FACTOR,
        wind_cost_factor=WIND_COST_CENTER_FACTOR,
        battery_cost_factor=BATTERY_COST_CENTER_FACTOR,
        hydrogen_cost_factor=HYDROGEN_COST_CENTER_FACTOR,
    )

    model = Model(name=f"{COLLECTION}", function=initialized_model)

    # levers / policies
    model.levers = [
        CategoricalParameter("scenario", RES_SCENARIOS),  # 6 options
        CategoricalParameter(
            "target_RE_strategy",
            [
                "current_projection_excl_export",
                "fixed_target_60",
                "fixed_target_80"
            ],
        ),  # 3 options
    ]
    # --> 18 policies

    # specify outcomes
    model.outcomes = [ScalarOutcome(metric) for metric in METRICS]

    # run experiments
    with MultiprocessingEvaluator(model, n_processes=4) as evaluator:
        results = evaluator.perform_experiments(policies=18, levers_sampling='ff')

    # with SequentialEvaluator(model) as evaluator:
    # results = evaluator.perform_experiments(scenarios=1, policies=5)

    # save results
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    results_file_name = RESULTS_FOLDER / f"{COLLECTION}_res_ema_results_{run_ID}.tar.gz"
    save_results(results, file_name=results_file_name)
