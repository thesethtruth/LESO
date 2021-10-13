import pandas as pd
import pandas as pd
import numpy as np
import plotly.express as pe
from pathlib import Path
import sys
import LESO
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

from LESO.experiments.analysis import (
    load_ema_leso_results,
    open_leso_experiment_file,
)
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% constants
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
sys.path.append(FOLDER.parent.absolute().__str__())
run_id = 210907

#%% load in results
experiments, outcomes, df = load_ema_leso_results(
    run_id=run_id, 
    exp_prefix="cablepooling",
    results_folder=RESULT_FOLDER)

#%% data selection
greenfield = df.query("subsidy_scheme == 'brownfield'").copy(deep=True)
exp = open_leso_experiment_file(RESULT_FOLDER / df.filename_export.iat[189])

spec_yield_pv = (
    sum(exp.components.pv1.state['power [+]']) /
    exp.components.pv1.settings.installed 
)
tot_yield_wind = sum(exp.components.wind1.state['power [+]'])

## change / add some data
pv_col = "PV South installed capacity"
greenfield['pv_cost_absolute'] = greenfield.pv_cost_factor * 1020
greenfield['curtailment'] = -greenfield['curtailment']
greenfield['total_generation'] = (greenfield[pv_col] * spec_yield_pv + tot_yield_wind)
greenfield['relative_curtailment'] = greenfield['curtailment'] / greenfield['total_generation'] *100
greenfield['total_installed_capacity'] = greenfield[pv_col] + 10



#%% Deployment vs absolut cost scatter

fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(6,2.2)
sns.scatterplot(
    x="pv_cost_absolute",
    y=pv_col,
    size='curtailment',
    hue='curtailment',
    data=greenfield,
    palette="Reds",
    ax=ax,
    edgecolor="black"
)

ax.set_ylabel("deployed PV capacity (MW)")
ax.set_ylim([-1, 20])

ax.set_xlabel("PV capacity cost (€/kWp)")
ax.set_xlim([380, 870])

ax.legend(frameon=False, title='Curtailment (MWh)')

default_matplotlib_save(fig, "report_cablepool_init_pv_deployment_vs_cost.png")

#%% relative curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,2.2)

sns.lineplot(
    x="total_installed_capacity",
    y="relative_curtailment",
    # size='curtailment',
    # hue='curtailment',
    data=greenfield,
    color="firebrick",
    ax=ax,
    # edgecolor="black"
)

ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 40])

ax.set_ylabel("relative curtailment (%)")
ax.set_ylim([0, 6])

default_matplotlib_save(fig, "report_cablepool_init_rel_curtailment_vs_deployment.png")

#%% absolute curtailment
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,2.2)

sns.lineplot(
    x="total_installed_capacity",
    y="curtailment",
    # size='curtailment',
    # hue='curtailment',
    data=greenfield,
    color='steelblue',
    ax=ax,
    # edgecolor="black"
)

ax.set_xlabel("total deployed capacity (MW)")
ax.set_xlim([0, 40])

ax.set_ylabel("absolute curtailment (MWh)")
ax.set_ylim([0, 3000])

default_matplotlib_save(fig, "report_cablepool_init_abs_curtailment_vs_deployment.png")

# %%
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax)
fig.set_size_inches(3,2.2)


sns.lineplot(
    x="total_generation",
    y="curtailment",
    # size='curtailment',
    # hue='curtailment',
    data=greenfield,
    color='steelblue',
    ax=ax,
    # edgecolor="black"
)
ax.axis("equal")
# %%
