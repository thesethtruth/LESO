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
    CategoricalParameter("grid_capacity", [7.5, 10, 12.5]),
]

# uncertainties / scenarios
model.uncertainties = [
    RealParameter("pv_cost_factor", 0.5, 1.1),
    RealParameter("battery_cost_factor", 0.5, 1.1),
]

# specify outcomes
model.outcomes = [ScalarOutcome(metric) for metric in METRICS]
