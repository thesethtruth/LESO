from evhub_leso_handshake import METRICS, EVHub

from ema_workbench import (
    RealParameter,
    CategoricalParameter,
    ScalarOutcome,
    Model,
    )

# initiate model
model = Model(name='EVHub', function=EVHub)

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
