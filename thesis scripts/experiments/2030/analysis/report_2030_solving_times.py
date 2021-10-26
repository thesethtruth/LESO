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
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
LEFT_MARGIN = 0.15
COLLECTION = "gld2030"
RUN_ID = "2310_v2"

## settings
filter = ("run_id", "=", RUN_ID)
df = gdatastore_results_to_df(COLLECTION, filter=filter)


print(f"Experiment progress: {len(df)} / 1000")
df.solving_time.describe()