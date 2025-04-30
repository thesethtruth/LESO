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
from cablepool_leso_handshake import METRICS, RESULTS_FOLDER, CablePooling, COLLECTION



if __name__ == "__main__":
    
    # initiate model
    ema_logging.log_to_stderr(ema_logging.INFO)
    
    run_ID = input('Please enter the run ID:')
    initialized_model = partial(CablePooling, run_ID=run_ID)
    model = Model(name=f"{COLLECTION}", function=initialized_model)

    # levers / policies
    model.levers = [
        CategoricalParameter("approach", ["no_subsidy", "subsidy"])
    ]

    # uncertainties / scenarios
    model.uncertainties = [
        RealParameter("pv_cost_factor", 0.38, 0.85),
        RealParameter("battery_cost_factor", 0.41, 0.70),
    ]
    # specify outcomes
    model.outcomes = [ScalarOutcome(metric) for metric in METRICS]

    # run experiments
    with MultiprocessingEvaluator(model, n_processes=10) as evaluator:
        results = evaluator.perform_experiments(scenarios=200, policies=2)
    
    # with SequentialEvaluator(model) as evaluator:
    #     results = evaluator.perform_experiments(scenarios=5, policies=2)

    # save results
    results_file_name = RESULTS_FOLDER / f"{COLLECTION}_ema_results_{run_ID}.tar.gz"
    save_results(results, file_name=results_file_name)

