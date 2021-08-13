import os
from cablepool_leso_handshake import METRICS, CablePooling, RESULT_FOLDER, RUNID

from ema_workbench import (
    RealParameter,
    CategoricalParameter,
    ScalarOutcome,
    perform_experiments,
    Model,
    save_results
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

# run experiments
results = perform_experiments(model, scenarios=100, policies=3)

# save results
results_file_name = os.path.join(RESULT_FOLDER, f"cabelpooling_ema_results_{RUNID}.tar.gz")
save_results(results, file_name=results_file_name)

