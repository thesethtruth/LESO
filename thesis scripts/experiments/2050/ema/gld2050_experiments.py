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
from gld2050_leso_handshake import METRICS, RESULTS_FOLDER, GLD2050


if __name__ == "__main__":
    
    # initiate model
    ema_logging.log_to_stderr(ema_logging.INFO)
    run_ID = input("Please enter the run ID:")
    GLD2050_w_runID = partial(GLD2050, run_ID=run_ID)
    model = Model(name="gld2050", function=GLD2050_w_runID)

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
        CategoricalParameter(
            "target_RE_strategy", 
            [
                "current_projection_excl_export",
                "fixed_target_80",
                "fixed_target_100",
            ],
        ),  # 3 options
        
    ]
    # --> 12 policies


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
    with MultiprocessingEvaluator(model, n_processes=10) as evaluator:
        results = evaluator.perform_experiments(scenarios=300, policies=12)
    
    # with SequentialEvaluator(model) as evaluator:
    #     results = evaluator.perform_experiments(scenarios=1, policies=5)

    # save results
    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    results_file_name = RESULTS_FOLDER / f"gld2050_ema_results_{run_ID}.tar.gz"
    save_results(results, file_name=results_file_name)

