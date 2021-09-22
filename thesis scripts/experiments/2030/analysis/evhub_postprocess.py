import pandas as pd
import numpy as np
import plotly.express as pe
from pathlib import Path
import sys
import plotly.graph_objects as go

import LESO.defaultvalues as defs

#%% constants

FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
sys.path.append(FOLDER.parent.absolute().__str__())
exp_prefix = "evhub"
run_id = 120903
wind_capex = defs.wind['capex']
pv_capex = defs.pv['capex']

#%% load in results
from LESO.experiments.analysis import (
    load_ema_leso_results,
    open_leso_experiment_file,
    quick_lcoe,
    annualized_cost
)

experiments, outcomes, df = load_ema_leso_results(run_id=run_id, exp_prefix=exp_prefix, results_folder=RESULT_FOLDER)
exp = open_leso_experiment_file(RESULT_FOLDER / df.filename_export[0])

wind_col = "Nordex N100 2500 installed capacity"
pv_col = "PV South installed capacity"
bat_col = "2h battery installed capacity"
#%% plots        
fig = go.Figure()
fig.add_trace(pe.scatter(
    df,
    x="solar_cost_factor",
    y="wind_cost_factor",
    color="curtailment",
))

fig.show()

if False:
    ## PV
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["pv_cost_factor"]*pv_capex,
        y=df[pv_col],
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
    fig.show()

    ## Wind
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["wind_cost_factor"]*wind_capex,
        y=df[wind_col],
        mode="markers",
    ))

    fig.update_layout(template="simple_white")
    fig.update_yaxes(
        ticksuffix = " MW",
        title="<b>Additional installed capacity of Wind</b>"
    )
    fig.update_xaxes(
        ticksuffix = " €/kWp",
        title= "<b>Cost price of wind</b>"
    )
    fig.show()

    ## Battery
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["battery_cost_factor"],
        y=df[bat_col],
        mode="markers",
    ))

    fig.update_layout(template="simple_white")
    fig.update_yaxes(
        ticksuffix = " MW",
        title="<b>Additional installed capacity of battery</b>"
    )
    fig.update_xaxes(
        ticksuffix = " €/kWp",
        title= "<b>Cost price of battery</b>"
    )
    fig.show()

    ## PV vs. Battery
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[bat_col],
        y=df[pv_col],
        mode="markers",
    ))

    fig.update_layout(template="simple_white")
    fig.update_xaxes(
        ticksuffix = " MW",
        title="<b>Installed capacity of battery</b>"
    )
    fig.update_yaxes(
        ticksuffix = " MW",
        title="<b>Installed capacity of PV</b>"
    )

    fig.show()

    ## Wind vs. Battery
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[bat_col],
        y=df[wind_col],
        mode="markers",
    ))

    fig.update_layout(template="simple_white")
    fig.update_xaxes(
        ticksuffix = " MW",
        title="<b>Installed capacity of battery</b>"
    )
    fig.update_yaxes(
        ticksuffix = " MW",
        title="<b>Installed capacity of wind</b>"
    )

    fig.show()

    ## Wind vs. PV
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[wind_col],
        y=df[pv_col],
        marker_size = (df["battery_cost_factor"]+df["wind_cost_factor"]+df["pv_cost_factor"])*7,
        mode="markers",
    ))

    fig.update_layout(template="simple_white")
    fig.update_xaxes(
        ticksuffix = " MW",
        title="<b>Installed capacity of wind</b>"
    )
    fig.update_yaxes(
        ticksuffix = " MW",
        title="<b>Installed capacity of solar</b>"
    )

    fig.show()