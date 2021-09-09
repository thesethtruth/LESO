import pandas as pd
import pandas as pd
import numpy as np
import plotly.express as pe
from pathlib import Path
import sys
import LESO
import plotly.graph_objects as go

#%% constants

FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
sys.path.append(FOLDER.parent.absolute().__str__())
run_id = 120901
# run_id = 120821
#%% load in results
from LESO.experiments.analysis import (
    load_ema_leso_results,
    open_leso_experiment_file,
    quick_lcoe,
    annualized_cost
)

experiments, outcomes, df = load_ema_leso_results(run_id=run_id, results_folder=RESULT_FOLDER)
exp = open_leso_experiment_file(RESULT_FOLDER / df.filename_export[0])

#%% plots        
fig = go.Figure()


fig.add_trace(go.Scatter(
    x=df["pv_cost_factor"]*0.8,
    y=df["PV South installed capactiy"],
    marker_size=df['PV South installed capactiy']*1,
    mode="markers",
))

fig.update_layout(template="simple_white")
fig.update_yaxes(
    ticksuffix = " MW",
    title="<b>Additional installed capacity of PV</b>"
)
fig.update_xaxes(
    ticksuffix = " €/kWp",
    title= "<b>Cost price of PV</b>"
)

# %%
