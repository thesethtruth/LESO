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
from gld2050_leso_handshake import METRICS, RESULTS_FOLDER, GLD2050, COLLECTION


if __name__ == "__main__":
    
    # initiate model
    ema_logging.log_to_stderr(ema_logging.INFO)


    run_ID = input("Please enter the run ID:")
    target_RE_strategy = "fixed_target_100"
    initialized_model = partial(GLD2050, run_ID=run_ID, target_RE_strategy=target_RE_strategy)
    model = Model(name=f"{COLLECTION}", function=initialized_model)

    # levers / policies
    model.levers = [
        CategoricalParameter(
            "scenario", 
            [
                'Gelderland_2050_regional',
                'Gelderland_2050_national',
                'Gelderland_2050_european',
                'Gelderland_2050_international'
            ],
        ),  # 4 options
    ] # --> 4 policies


    # uncertainties / scenarios
    model.uncertainties = [
        RealParameter("pv_cost_factor", 0.25, 0.72),
        RealParameter("wind_cost_factor", 0.67, 0.95),
        RealParameter("battery_cost_factor", 0.25, 0.70),
        RealParameter("hydrogen_cost_factor", 0.13, 0.53),
    ]

    # specify outcomes
    model.outcomes = [ScalarOutcome(metric) for metric in METRICS]

    # run experiments
    with MultiprocessingEvaluator(model, n_processes=10) as evaluator:
        results = evaluator.perform_experiments(scenarios=250, policies=4)
    
    # save results
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    results_file_name = RESULTS_FOLDER / f"{COLLECTION}_ema_results_{run_ID}.tar.gz"
    save_results(results, file_name=results_file_name)

