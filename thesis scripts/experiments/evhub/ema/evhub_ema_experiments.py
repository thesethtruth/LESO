from functools import partial
from ema_workbench import (
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
from evhub_leso_handshake import METRICS, RESULTS_FOLDER, EVHub, COLLECTION



if __name__ == "__main__":
    
    # initiate model
    ema_logging.log_to_stderr(ema_logging.INFO)
    
    run_ID = input('Please enter the run ID:')
    initialized_model = partial(EVHub, run_ID=run_ID)
    model = Model(name=f"{COLLECTION}", function=initialized_model)

    # levers / policies
    model.levers = [
        CategoricalParameter("grid_capacity", [0, 0.5, 1, 1.5]),
    ]

    # uncertainties / scenarios
    model.uncertainties = [
        RealParameter("pv_cost_factor", 0.38, 0.85),
        RealParameter("wind_cost_factor", 0.77, 0.98),
        RealParameter("battery_cost_factor", 0.41, 0.70),
    ]

    # specify outcomes
    model.outcomes = [ScalarOutcome(metric) for metric in METRICS]

    # run experiments
    with MultiprocessingEvaluator(model, n_processes=2) as evaluator:
        results = evaluator.perform_experiments(scenarios=1, policies=4)
    
    # with SequentialEvaluator(model) as evaluator:
    #     results = evaluator.perform_experiments(scenarios=5, policies=2)

    # save results
    results_file_name = RESULTS_FOLDER / f"{COLLECTION}_ema_results_{run_ID}.tar.gz"
    save_results(results, file_name=results_file_name)

