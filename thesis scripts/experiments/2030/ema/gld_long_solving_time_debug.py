#%%

import ema_workbench
from pathlib import Path
from ema_workbench import experiments_to_scenarios
from ema_workbench.em_framework import (
    SequentialEvaluator,
    MultiprocessingEvaluator,
    Model,
    CategoricalParameter,
    RealParameter,
    ScalarOutcome
)
import numpy as np
from gld2030_leso_handshake import GLD2030
from functools import partial
from gld2030_definitions import COLLECTION, METRICS
from LESO.experiments.analysis import gdatastore_results_to_df

#%% experiments for reference of the format
# ema_results_path = r"C:\Users\Sethv\#Universiteit Twente\GIT\LESO\thesis scripts\experiments\evhub\results\evhub_ema_results_210907.tar.gz"
# experiments, outcomes = ema_workbench.load_results(ema_results_path)

#%%

## constants
LEFT_MARGIN = 0.15
COLLECTION = "gld2030"
RUN_ID = "2310_v2"

## settings
filters = [
    ("run_id", "=", RUN_ID),
    ("target_RE_strategy", "=", "fixed_target_100"),
]
df = gdatastore_results_to_df(COLLECTION, filters=filters)
uncertainties = [col for col in df.columns if "cost_factor" in col]
selection = (df
    .sort_values("solving_time", ascending=False)
    .head(50)
)[[*uncertainties, "solving_time"]]

experiments = selection[uncertainties].reset_index(drop=True)

#%%

scenarios = experiments_to_scenarios(experiments)

#%%
if __name__ == "__main__":
    SCENARIO = "2030Gelderland_laag"
    target_RE_strategy = "fixed_target_100"

    run_ID = input("Please enter the run ID:")
    initialized_model = partial(GLD2030, run_ID=run_ID, scenario=SCENARIO, target_RE_strategy=target_RE_strategy)

    model = Model(name=f"{COLLECTION}", function=initialized_model)
    # specify outcomes
    model.outcomes = [ScalarOutcome(metric) for metric in METRICS]

    with MultiprocessingEvaluator(model, n_processes=10) as evaluator:
        results = evaluator.perform_experiments(scenarios=scenarios)
