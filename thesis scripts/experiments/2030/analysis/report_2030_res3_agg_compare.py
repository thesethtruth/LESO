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


color = {
    "PV": "#edc645",
    "wind": "steelblue",
    "battery": "darkseagreen",
    "grid": "darkgrey",
}
features = [pv_col, wind_col, total_bat_col]

#%% load in results
RUN_ID = "3010_RES2"
db = get_data_from_db(collection=COLLECTION, run_id=RUN_ID, force_refresh=False)
res_60 = db.query("target_RE_strategy == 'fixed_target_60'").copy()
res_60 = res_60[features]
RUN_ID = "gldcompare"
gld_60 = get_data_from_db(collection=COLLECTION, run_id=RUN_ID, force_refresh=False)
gld_60 = gld_60[features]

df_barplot = pd.DataFrame(
    data = np.hstack([res_60.sum().values, gld_60.values.flat]).reshape(2,3),
    columns = res_60.columns,
    index = ["RES regions aggregated", "Province of Gelderland"]
)

df_barplot.rename({
    pv_col: "PV",
    wind_col: "wind",
    total_bat_col: "battery",
}, inplace=True, axis=1)

#%%
fig, ax = plt.subplots()
fig, ax = default_matplotlib_style(fig, ax, decrease_legend=False)
fig.set_size_inches(4,3)
color={"PV": "#edc645", "wind": "steelblue", 'battery': "darkseagreen", "grid": "darkgrey"}
df_barplot.plot.bar(stacked=True, ax=ax, color=color)

ax.set_ylabel("total capacity (MW(h))")
ax.set_xticklabels(["RES regions \n aggregated", "Province \nGelderland"], rotation = 0, fontsize=9)
ax.legend(
    bbox_to_anchor=(1.02, 0.5),
    loc=6,
    borderaxespad=0.0,
    frameon=False,
)


for c in ax.containers:
    v = c[0]
    # Optional: if the segment is small or 0, customize the labels
    if c.get_label() == "grid":
        labels = [round(v.get_height(),1) if v.get_height() > 0 else '' for v in c]
    else:
        labels = [(int(v.get_height()) if v.get_height() > 1 else round(v.get_height(),1)) if v.get_height() > 0.1 else '' for v in c]
    
    # remove the labels parameter if it's not needed for customized labels
    ax.bar_label(c, labels=labels, label_type='center', color="#404040")

default_matplotlib_save(fig, IMAGE_FOLDER / f"report_{COLLECTION}_configurations_agg_compare.png")