#%% AAAAHHHHH.py
from LESO.experiments import open_leso_experiment_file
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from profile_plotting import plot_experiment_curves

FOLDER = Path(__file__).parent
EXPERIMENTS_FOLDER = FOLDER / "experiments"

starts = [700, 3000]
duration = 7

exp_filenames = {
    "evhub_00mw_": "evhub_exp_210285.json",
    # "evhub_05mw_": "evhub_exp_717774.json",
    "evhub_10mw_": "evhub_exp_711889.json",
    # "evhub_15mw_": "evhub_exp_227895.json",
    "cablepooling_": "cablepooling_exp_162076137670371.json",
}

for fig_filename, experiment_file in exp_filenames.items():

    for start in starts:
        plot_experiment_curves(
            experiment_file=experiment_file,
            start=start,
            duration=duration,
            fig_filename=fig_filename,
            include_only_battery=True,
        )