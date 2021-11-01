# report_2030_gld1_heatmaps.py
# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from LESO.plotting import PAD, FONTSIZE
from util_2030_postprocess_tools import (
    get_data_from_db,
    gcloud_read_experiment,
    pv_col,
    wind_col,
    bat2_col,
    bat6_col,
    bat10_col,
    total_bat_col,
    total_h2_col,
    batcols,
    bivar_tech_dict,
    grid_col,
)

#%% paths
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
COLLECTION = "gld2030"
RUN_ID = "2310_v2"
palette = "mako"
cmap = sns.diverging_palette(190, 130, l=50, s=90, as_cmap=True)
FIG_FONTSIZE = 10
HM_FONTSIZE = 9
decrease_legend = False
#%%
## maps
hm_col_map = {
    pv_col: 'PV power',
    wind_col: 'wind power',
    total_bat_col: 'battery storage',
    total_h2_col: 'hydrogen storage',
    'pv_cost_factor': 'PV cost',
    'wind_cost_factor': 'wind cost',
    'battery_cost_factor': 'battery cost',
    "hydrogen_cost_factor" : "hydrogen cost",
    'objective_result': 'system cost',
    'total_generation': 'total generation',
}
features = list(hm_col_map.values())
targets = {
    "no_target": {"title": "No target", "clusters": 2},
    "fixed_target_60": {"title": "60% target", "clusters": 3},
    "fixed_target_80": {"title": "80% target", "clusters": 3},
    "fixed_target_100": {"title": "100% target", "clusters": 4},
}


#%% fetch data
db = get_data_from_db(collection=COLLECTION, run_id=RUN_ID, force_refresh=False)

## rename columns
db.rename(hm_col_map, inplace=True, axis=1)


#%% =================================================================================================
##                      HEATMAPS



for i, (target, settings) in enumerate(targets.items()):

    # select the grid capacity
    df = db.query(f"target_RE_strategy == '{target}'").copy()
    

    # subset-df
    sdf = df[features].copy()

    # plot
    fig, ax = plt.subplots()
    fig.set_size_inches(5, 5)
    rc = {
        "font.family": "Open Sans",
        "font.size": FIG_FONTSIZE,
    }
    plt.rcParams.update(rc)

    cbar_ax = fig.add_axes([0.9, 0.75, 0.02, 0.2])

    # calculate corr matrix
    corr_mat = sdf.corr(method="pearson")
    mask = np.zeros_like(corr_mat)
    mask[np.triu_indices_from(mask)] = True

    figgy = sns.heatmap(
        corr_mat,
        ax=ax,
        mask=mask,
        square=True,
        annot=True,
        fmt=".1f",
        annot_kws={"fontsize": HM_FONTSIZE},
        vmin=-1,
        vmax=1,
        cmap=cmap,
        cbar_ax=cbar_ax,
    )

    # ax.text(
    #     0.45,
    #     1,
    #     settings["title"],
    #     horizontalalignment="center",
    #     verticalalignment="center",
    #     transform=ax.transAxes,
    #     fontdict={
    #         "fontsize": 10,
    #     },
    # )


    default_matplotlib_save(
        fig, IMAGE_FOLDER / f"report_{COLLECTION}_correlation_matrix_{target}.png"
    )

# %%
if input("Crop the images in this folder? [y/n]") == "y":
    from LESO.plotting import crop_transparency_top_bottom

    crop_transparency_top_bottom(
        folder_to_crop=IMAGE_FOLDER, file_ext_to_crop="png", override_original=True, crop_top=True,
    )
