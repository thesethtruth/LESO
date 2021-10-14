# ema post-analysis

from pathlib import Path
import sys

import pandas as pd
import numpy as np
import plotly.express as pe
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns

import LESO.defaultvalues as defs
from LESO.experiments.analysis import (
    load_ema_leso_results,
)

#%% constants

FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
sys.path.append(FOLDER.parent.absolute().__str__())
exp_prefix = "evhub"
run_id = 210907
wind_capex = defs.wind['capex']
pv_capex = defs.pv['capex']

#%% load in results
from ema_workbench.analysis import prim, feature_scoring


experiments, outcomes, df = load_ema_leso_results(run_id=run_id, exp_prefix=exp_prefix, results_folder=RESULT_FOLDER)

x = experiments

## curtailment
y = outcomes['curtailment'] > -600
prim_alg = prim.Prim(x, y, threshold= -600)
box1 = prim_alg.find_box()
box1.show_pairs_scatter()
plt.figure()


#%% battery installed
y = outcomes['2h battery installed capacity'] < 5
prim_alg = prim.Prim(x, y, threshold=0.5)
box1 = prim_alg.find_box()
box1.show_pairs_scatter()
plt.figure()

y = outcomes
fs = feature_scoring.get_feature_scores_all(x, y)
sns.heatmap(fs, cmap='viridis', annot=True)
plt.show()