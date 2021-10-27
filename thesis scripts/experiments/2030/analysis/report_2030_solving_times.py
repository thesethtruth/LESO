# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from LESO.experiments.analysis import gdatastore_results_to_df


from LESO.plotting import default_matplotlib_save, default_matplotlib_style


#%% paths
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent  / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
LEFT_MARGIN = 0.15
COLLECTION = "gld2030"
RUN_ID = "2310_v2"

#%% get results

## Original results
filters = [
    ("run_id", "=", RUN_ID),
    ("target_RE_strategy", "=", "fixed_target_100"),
]
df = gdatastore_results_to_df(COLLECTION, filters=filters)

selection = (df
    .sort_values("solving_time", ascending=False)
    .head(50)
)


## rerun with 0 crossover, 2 method and BarConvTol e-5
run_id_rerun_cases = "test_longsolve"
filters = [
    ("run_id", "=", run_id_rerun_cases),
    ("target_RE_strategy", "=", "fixed_target_100"),
]
rerun_df = gdatastore_results_to_df(COLLECTION, filters=filters)
rerun_df = rerun_df.sort_values("hydrogen_cost_factor", ascending=False)

#%% compare data
capacity_columns = [col for col in rerun_df if "installed capacity" in col]
compare_df = pd.DataFrame(columns=capacity_columns)
for name, row in selection.iterrows():
    
    row_id = row.filename_export.replace(".json", "")
    matched_rerun = rerun_df[
        rerun_df.hydrogen_cost_factor == row.hydrogen_cost_factor
    ]
    matched_rerun = matched_rerun.iloc[0,:][capacity_columns]

    compare_df.loc[row_id+"_original", :] = row[capacity_columns]
    compare_df.loc[row_id+"_retro", :] = matched_rerun




#%%
print_solving_times = False
if print_solving_times:
    #%%
    gdf = df.groupby("target_RE_strategy")
    for name, g in gdf:
        print(name)
        print(g["solving_time"].describe())
        print()
        print()
        