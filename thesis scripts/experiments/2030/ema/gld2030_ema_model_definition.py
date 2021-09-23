from functools import partial

from LESO.defaultvalues import scenarios_2030

from gld2030_leso_handshake import METRICS, GLD2030

from ema_workbench import (
    RealParameter,
    CategoricalParameter,
    ScalarOutcome,
    Model,
)

# initiate model
run_ID = input("Please enter the run ID:")
GLD2030_w_runID = partial(GLD2030, run_ID=run_ID)

model = Model(name="gld2030", function=GLD2030_w_runID)

# levers / policies
model.levers = [
    CategoricalParameter("scenario", list(scenarios_2030.keys())), # 8 options
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

# uncertainties / scenarios
model.uncertainties = [
    RealParameter("pv_cost_factor", 0.38, 0.85),
    RealParameter("wind_cost_factor", 0.77, 0.98),
    RealParameter("battery_cost_factor", 0.41, 0.70),
    RealParameter("hydrogen_cost_factor", 0.37, 0.69),
]

# specify outcomes
model.outcomes = [ScalarOutcome(metric) for metric in METRICS]
