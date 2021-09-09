# cablepool_compare.py

import pandas as pd
from pathlib import Path

from LESO.experiments.analysis import load_ema_leso_results, open_leso_experiment_file

RESULTS_FOLDER = Path(__file__).parent.parent / "results"

# earlier run of experiments
run_id = 120821
*_, df1 = load_ema_leso_results(
    run_id=run_id, exp_prefix="cablepooling", results_folder=RESULTS_FOLDER
)
subsection = df1[df1["Li-ion EES installed capactiy"] > 3]
file_to_inspect1 = subsection[
    subsection.battery_cost_factor == subsection.battery_cost_factor.min()
    ].filename_export.iat[0]
system1 = open_leso_experiment_file(RESULTS_FOLDER / file_to_inspect1)
battery_settings1 = system1.components.lithium1.settings
grid_settings1 = system1.components.grid1.settings


def lithium_old_capex(settings):
    cpx = settings.capex
    cpxr = settings.capex_EP_ratio
    epr = settings.EP_ratio
    return cpx * (1 - cpxr) / epr + cpx * cpxr


old_capex = lithium_old_capex(battery_settings1)
old_opex = battery_settings1.opex
old_crf = 0.054046819516284
old_ac = old_capex * old_crf + old_opex

# later run of experiments
run_id = 120901
*_, df2 = load_ema_leso_results(
    run_id=run_id, exp_prefix="cablepooling", results_folder=RESULTS_FOLDER
)
file_to_inspect2 = df2[
    df2.battery_cost_factor == df2.battery_cost_factor.min()
].filename_export.iat[0]
system2 = open_leso_experiment_file(RESULTS_FOLDER / file_to_inspect2)
battery_settings2 = system2.components.lithium2h_1.settings


def lithium_new_capex(settings):
    cpxs = settings.capex_storage
    cpxp = settings.capex_power
    epr = settings.EP_ratio
    return (cpxs * epr + cpxp) / epr


def lithium_new_opex(settings):
    return lithium_new_capex(settings) * settings.EP_ratio * settings.opex_ratio


new_capex = lithium_new_capex(battery_settings2)
new_opex = lithium_new_opex(battery_settings2)
new_crf = 0.08290341166238394  # from LESO.Lithium.crf
new_ac = new_capex * new_crf + new_opex

print("-- capex --")
print(f"old: {round(old_capex,2)}, new: {round(new_capex,2)}")
print("-- opex --")
print(f"old: {round(old_opex,4)}, new: {round(new_opex,4)}")
print("-- crf --")
print(f"old: {round(old_crf,4)}, new: {round(new_crf,4)}")
print("-- annuity --")
print(f"old: {round(1/old_crf,2)}, new: {round(1/new_crf,2)}")
print("-- annualized cost --")
print(f"old: {round(old_ac,4)}, new: {round(new_ac,4)}")
