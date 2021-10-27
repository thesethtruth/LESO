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
from gld2030_leso_handshake import METRICS, RESULTS_FOLDER, GLD2030, COLLECTION


if __name__ == "__main__":
    
    # initiate model
    ema_logging.log_to_stderr(ema_logging.INFO)

    SCENARIO = "2030Gelderland_laag"
    run_ID = input("Please enter the run ID:")
    initialized_model = partial(GLD2030, run_ID=run_ID, scenario=SCENARIO)
    model = Model(name=f"{COLLECTION}", function=initialized_model)

    # levers / policies
    model.levers = [
        CategoricalParameter(
            "target_RE_strategy", 
            [
                "no_target",
                # "current_projection_include_export", not relevant
                # "current_projection_excl_export", only interesting under static cost
                "fixed_target_60",
                "fixed_target_80",
                "fixed_target_100",
            ],
        ),  # 4 options
    ]
    # --> 4 policies


    # uncertainties / scenarios
    model.uncertainties = [
        RealParameter("pv_cost_factor", 0.38, 0.85),
        RealParameter("wind_cost_factor", 0.77, 0.98),
        RealParameter("battery_cost_factor", 0.41, 0.70),
        RealParameter("hydrogen_cost_factor", 0.37, 0.69),
    ]

    # specify outcomes
    model.outcomes = [ScalarOutcome(metric) for metric in METRICS]

    # run experiments
    with MultiprocessingEvaluator(model, n_processes=6) as evaluator:
        results = evaluator.perform_experiments(scenarios=250, policies=4)
    
    # with SequentialEvaluator(model) as evaluator:
        # results = evaluator.perform_experiments(scenarios=1, policies=4)

    # save results
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    results_file_name = RESULTS_FOLDER / f"{COLLECTION}_ema_results_{run_ID}.tar.gz"
    save_results(results, file_name=results_file_name)

