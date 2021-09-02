from cablepool_leso_handshake import METRICS, CablePooling

from ema_workbench import (
    RealParameter,
    CategoricalParameter,
    ScalarOutcome,
    Model,
    )

# initiate model
model = Model(name='Cablepool', function=CablePooling)

# levers / policies
model.levers = [
    CategoricalParameter("subsidy_scheme", [1, 0]),
]

# uncertainties / scenarios
model.uncertainties = [
    RealParameter("pv_cost_factor", 0.38, 0.85),
    RealParameter("battery_cost_factor", 0.41, 0.70),
]

# specify outcomes
model.outcomes = [ScalarOutcome(metric) for metric in METRICS]
