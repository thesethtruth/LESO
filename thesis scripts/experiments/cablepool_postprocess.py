import ema_workbench
import os
from ema_workbench import experiments_to_scenarios
import pandas as pd
from tinydb import TinyDB
from models.experiments_overview import RESULT_FOLDER
import pandas as pd
import numpy as np

RESULT_FOLDER = "C:\\Users\\sethv\\Google Drive\\0 Thesis\\Results\\cablepooling"

ema_results = "cabelpooling_ema_results_120821.tar.gz"
ema_results_path = os.path.join(RESULT_FOLDER, ema_results)
experiments, outcomes = ema_workbench.load_results(ema_results_path)

data = pd.DataFrame(outcomes)

data["total_installed_capacity"] = data.iloc[:, :4].sum(axis=1)
data["additional_installed_capacity"] = data.iloc[:, :3].sum(axis=1)
data["volume_per_peak"] = data.total_renewable_energy / data.total_installed_capacity


db_file = "cablepooling_db120821.json"
db_path = os.path.join(RESULT_FOLDER, db_file)
db = TinyDB(db_path)


def convert_db_to_df(db):
    """Note that this is not stable for non-structured (e.g. document-type) dbs"""
    df = pd.DataFrame(
        {key: [document.get(key, None) for document in db] for key in db.all()[0]}
    )

    return df


df = convert_db_to_df(db)
df["total_installed_capacity"] = df.iloc[:, :4].sum(axis=1)
df["additional_installed_capacity"] = df.iloc[:, :3].sum(axis=1)
df["volume_per_peak"] = df.total_renewable_energy / df.total_installed_capacity
df["curtailment"] = abs(df.curtailment)
df.sort_values(by="pv_cost_factor")

#%%
grid_7_5 = df[df.grid_capacity == 7.5]
grid_10 = df[df.grid_capacity == 10]
grid_12_5 = df[df.grid_capacity == 12.5]

grid_7_5.sort_values(by="pv_cost_factor")

#%% reading a json
import json
from LESO import AttrDict

to_read = df.filename_export[0]
fp_simulation_json = os.path.join(RESULT_FOLDER, to_read)
with open(fp_simulation_json) as infile:
    simulation = AttrDict(json.load(infile))

# since:
# objective = (system.crf*(unit_capex)+fixed_cost)*pyoVar + variable_cost
def get_objective(
    system_crf, 
    investment_cost, 
    fixed_cost, 
    installed_capacity, 
    exported_electricity,
    SDE_price,
):
    return (
        system_crf * investment_cost + fixed_cost
    ) * installed_capacity - exported_electricity* SDE_price


wind = simulation.components.wind1
grid = simulation.components.grid1
system_crf = 0.054046819516284
wind_power_curve = sum(wind.state["power [+]"])
wind_power_curve_constrained = sum(np.where(np.array(wind.state["power [+]"]) > 7.5, 7.5, wind.state["power [+]"]))


wind_plain_objective = get_objective(
    system_crf=system_crf,
    investment_cost=wind.settings.capex,
    fixed_cost=wind.settings.opex,
    installed_capacity=wind.settings.installed,
    exported_electricity=wind_power_curve,
    SDE_price=grid.settings.variable_income
)

wind_plain_objective_constrained = get_objective(
    system_crf=system_crf,
    investment_cost=wind.settings.capex,
    fixed_cost=wind.settings.opex,
    installed_capacity=wind.settings.installed,
    exported_electricity=wind_power_curve_constrained,
    SDE_price=grid.settings.variable_income
)

# %% plotting
plot = False

if plot:
    import plotly.express as pe

    fig = pe.scatter(
        grid_7_5,
        x="pv_cost_factor",
        y="battery_cost_factor",
        size="total_renewable_energy",
        color="curtailment",
        color_continuous_scale="algae",
    )
    fig.update_layout(template="simple_white")
    fig.show()

    fig = pe.scatter(
        grid_7_5,
        x="additional_installed_capacity",
        y="curtailment",
        color="battery_cost_factor",
        size=df.columns[4],
    )
    fig.update_layout(template="simple_white")
    fig.show()
    # %%
