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
    CategoricalParameter("charging_fee", [350, 600]),
]

# uncertainties / scenarios
model.uncertainties = [
    RealParameter("pv_cost_factor", 0.38, 0.85),
    RealParameter("wind_cost_factor", 0.77, 0.98),
    RealParameter("battery_cost_factor", 0.41, 0.70),
]

# specify outcomes
model.outcomes = [ScalarOutcome(metric) for metric in METRICS]
