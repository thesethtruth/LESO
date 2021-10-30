# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt


from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from util_2030_postprocess_tools import (
    get_data_from_db,
    gcloud_read_experiment,
    pv_col,
    wind_col,
    bat2_col,
    bat6_col,
    bat10_col,
    total_bat_col,
    batcols,
    bivar_tech_dict
)

#%%
## constants
COLLECTION = "gld2030"
RUN_ID = "3010_RES"

#%% load in results
db = get_data_from_db(
    collection=COLLECTION,
    run_id=RUN_ID,
    force_refresh=True
)
#%%
targets = db.target_RE_strategy.unique()
col_map = {
    pv_col: "PV",
    wind_col: "wind",
    total_bat_col: "battery"
}
color={"PV": "#edc645", "wind": "steelblue", 'battery': "darkseagreen", "grid": "darkgrey"}
for target in targets:
    df = db.query(f"target_RE_strategy == '{target}'")
    subdf = df[[pv_col, wind_col, total_bat_col, "scenario"]].copy()
    subdf.rename(col_map, inplace=True, axis=1)