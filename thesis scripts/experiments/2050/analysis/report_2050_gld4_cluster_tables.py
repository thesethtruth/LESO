# report_2030_gld1_heatmaps.py
# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from seaborn import palettes
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.collections import PolyCollection
from LESO.attrdict import AttrDict

from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from LESO.plotting import PAD, FONTSIZE
from util_2050_postprocess_tools import (
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
    clusters_translation,
    cluster_names
)

#%% paths
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
COLLECTION = "gld2050"
RUN_ID = "2710_v2"
palette = sns.color_palette("mako", n_colors=4)

cost_combinations = [
    ("pv cost factor", "PV"),
    ('wind cost factor',"wind"),
    ('battery cost factor',"battery"),
    ('hydrogen cost factor',"hydrogen"),
    ]

features = [x[1] for x in cost_combinations]
cost_factors = [x[0] for x in cost_combinations]


#%% fetch and process data
db = pd.read_pickle(RESOURCE_FOLDER / f"{COLLECTION}_2210_v2_clustered_named.pkl")
db['generic_clusters'] = db['cluster_names'].apply(lambda x: x.split(" (")[0])


#%%
ref_values = [1020, 1350, 340, 31]
gdf = db.groupby("scenario")

di = AttrDict()

for scenario, df in gdf:
    print(scenario)
    df.sort_values("sort",inplace=True)
    ggdf = df.groupby("cluster_names")

    di.update({scenario: AttrDict()})
    for cluster_name, dff in ggdf:
        df.sort_values("sort",inplace=True)
        
        fdf = dff[[*features]]
        cdf = dff[[*cost_factors]]
        cdf = cdf*ref_values
        
        mean_cost_values = cdf.mean()
        mean_design = fdf.mean()
        
        costs = cdf*mean_design.values
        
        max_cost = costs.sum(axis=1).max()
        min_cost = costs.sum(axis=1).min()
        mean_cost = sum(mean_design*mean_cost_values.values)
      
        name = cluster_name.split(" (")[0]
        
        di[scenario].update({name: {
            "min_cost": min_cost,
            "mean_cost": mean_cost,
            "max_cost": max_cost,
            "mean_cost_values": mean_cost_values.values,
            "mean_design": mean_design.values
            }
        })

for scenario in di.keys():

    for clustera in di[scenario].keys():

        for clusterb in di[scenario].keys():
            
            di[scenario][clustera].update({clusterb: 
            sum(di[scenario][clustera]['mean_design']*di[scenario][clusterb]['mean_cost_values']
            )})



output = dict()
clusters = db.generic_clusters.unique()

for scenario in di.keys():
    output.update({scenario: dict()})

    for cluster, dii in di[scenario].items():

        insert_dict = {
            c: dii[c]/dii['mean_cost'] for c in clusters
        }
        insert_dict.update({
            "worst case": dii['max_cost']/dii['mean_cost'],
            "best case": dii['min_cost']/dii['mean_cost']
        })
    
        output[scenario].update({
            cluster: insert_dict
        })

# %%
reform = {(outerKey, innerKey): values for outerKey, innerDict in output.items() for innerKey, values in innerDict.items()}
out_df = pd.DataFrame.from_dict(reform)

#%%
cmap = sns.diverging_palette(130, 190, l=50, s=90, as_cmap=True)
for scenario, _ in out_df.columns:
    plot_df = out_df[scenario][[*clusters]]

    df = plot_df.style.background_gradient(cmap=cmap).format("{:.2f}")
   
    p = IMAGE_FOLDER / f"report_correlation_table_latex_{scenario}.txt"
    with open(p, 'w') as file:
        file.write(df.to_latex(convert_css=True))



# %%
    
    # fig, ax = plt.subplots(
    #     figsize=(5, 3)
    # )
    # plt.tight_layout(pad=PAD)
    
    # rc = {
    #     "font.family": "Open Sans",
    #     "font.size": 10,
    #     "legend.fontsize": 8,
    # }
    # plt.rcParams.update(rc)
    
    # sns.heatmap(plot_df, cmap = cmap, annot=True, fmt=".2f", ax=ax,cbar=False)

    # ax.set_ylabel("cost condition")
    # ax.set_xlabel("system configuration")

