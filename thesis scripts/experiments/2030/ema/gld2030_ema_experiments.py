from functools import partial
from ema_workbench import perform_experiments, save_results
from ema_workbench import (
    RealParameter,
    CategoricalParameter,
    ScalarOutcome,
    Model,
)

from LESO.defaultvalues import scenarios_2030
from gld2030_leso_handshake import METRICS, RESULTS_FOLDER, GLD2030

SCENARIO = "2030Gelderland_laag"
# initiate model
run_ID = input("Please enter the run ID:")
GLD2030_w_runID = partial(GLD2030, run_ID=run_ID)

model = Model(name="gld2030", function=GLD2030_w_runID)

# levers / policies
model.levers = [
    CategoricalParameter("scenario", [SCENARIO]), # 1 options
    CategoricalParameter(
        "target_RE_strategy", 
        [
            "no_target",
            "current_projection_w_export",
            "current_projection_no_export"
            "fixed_target_60"
            "fixed_target_80",
        ],
    ),  # 5 options
]
# --> 40 policies


# uncertainties / scenarios
model.uncertainties = [
    RealParameter("pv_cost_factor", 0.38, 0.85),
    RealParameter("wind_cost_factor", 0.77, 0.98),
    RealParameter("battery_cost_factor", 0.41, 0.70),
    RealParameter("hydrogen_cost_factor", 0.37, 0.69),
]

# specify outcomes
model.outcomes = [ScalarOutcome(metric) for metric in METRICS]

###############################################################################

# run experiments
results = perform_experiments(model, scenarios=1, policies=40)

# save results
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
results_file_name = RESULTS_FOLDER / f"gld2030_ema_results_{run_ID}.tar.gz"
save_results(results, file_name=results_file_name)

