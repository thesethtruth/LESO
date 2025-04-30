# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt


from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from util_2030_postprocess_tools import (
    plot_grouped_stackedbars,
    get_data_from_db,
    gcloud_read_experiment,
    pv_col,
    wind_col,
    bat2_col,
    bat6_col,
    bat10_col,
    total_bat_col,
    batcols,
    bivar_tech_dict,
    grid_col,
)

#%%
## constants
FOLDER = Path(__file__).parent
RESOURCE_FOLDER = FOLDER / "resources"
IMAGE_FOLDER = FOLDER / "images"
IMAGE_FOLDER.mkdir(exist_ok=True)
RESOURCE_FOLDER.mkdir(exist_ok=True)

COLLECTION = "gld2030"
RUN_ID = "3010_RES2"

#%% load in results
db = get_data_from_db(collection=COLLECTION, run_id=RUN_ID, force_refresh=False)
#%%
targets = db.target_RE_strategy.unique()
col_map = {pv_col: "PV", wind_col: "wind", total_bat_col: "battery", grid_col: "grid"}
db.rename(col_map, inplace=True, axis=1)
idx_map = {
    "2030RES_Foodvalley ": "Foodvalley",
    "2030RES_NoordVeluwe": "Noord-Veluwe",
    "2030RES_ArnhemNijmegen": "Arnhem Nijmegen",
    "2030RES_Rivierenland": "Rivierenland",
    "2030RES_Cleantech": "Cleantech",
    "2030RES_Achterhoek": "Achterhoek",
}
db.set_index("scenario", inplace=True)
db.rename(idx_map, inplace=True, axis=0)
db.set_index("target_RE_strategy", inplace=True, append=True)
color = {
    "PV": "#edc645",
    "wind": "steelblue",
    "battery": "darkseagreen",
    "grid": "darkgrey",
}

#%%


subdb = db[["PV", "wind", "battery"]].copy()
subdb.sort_index(inplace=True)


ax, fig = plot_grouped_stackedbars(
    subdb,
    ix_entities_compared="target_RE_strategy",
    ix_categories="scenario",
    colors=color,
    figsize=(6, 4),
    ylabel= "deployed capacity (MW(h))"
)


labels = [i.replace(" ", "\n").replace("-", "\n") for i in sorted(idx_map.values())]
ax.set_xticks([i-0.1 for i in ax.get_xticks()])

ax.set_xticklabels(labels, rotation = 0, fontsize=9)






labels = [" current projection", " 60% target", " 80% target"]

heights = [1230, 1000, 1050]
heights.reverse()
k = 0
for i, rect in enumerate(ax.patches):

    if not i % 18:

        ax.text(
            rect.get_x() + rect.get_width()/2 -0.03, heights[k], labels[k], ha="left", va="bottom", rotation=90, fontsize=7, color="#3b3b3b"
        )
        k += 1
fig, ax = default_matplotlib_style(fig, ax)

ax.xaxis.set_ticks_position('none') 
default_matplotlib_save(fig, filename=IMAGE_FOLDER / "report_2030_res_compare_barplots.png")