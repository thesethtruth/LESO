import ema_workbench
import os
from ema_workbench import experiments_to_scenarios
from ema_workbench.em_framework import SequentialEvaluator
import numpy as np
from cablepool_leso_handshake import METRICS

RESULT_FOLDER = "C:\\Users\\sethv\\Google Drive\\0 Thesis\\Results\\cablepooling"

ema_results = "cabelpooling_ema_results_120821.tar.gz"
ema_results_path = os.path.join(RESULT_FOLDER, ema_results)
experiments, outcomes = ema_workbench.load_results(ema_results_path)

scenarios = experiments_to_scenarios(experiments)

from cablepool_ema_model_definition import model

def printer(**kwargs):
    # for key, value in kwargs.items():
    #     print(f"{key}: {value}")

    return {
        key: np.random.random()
        for key in METRICS
    }

model.function = printer

with SequentialEvaluator(model) as evaluator:
    results = evaluator.perform_experiments(scenarios=scenarios)

