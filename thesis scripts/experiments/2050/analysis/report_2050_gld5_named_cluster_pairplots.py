
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

from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from LESO.plotting import PAD, FONTSIZE

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
features=['PV', 'wind', 'battery', 'hydrogen']
costs = ['pv cost factor',
 'wind cost factor',
 'battery cost factor',
 'hydrogen cost factor']

#%% Data fetch
db = pd.read_pickle(RESOURCE_FOLDER / f"{COLLECTION}_2210_v2_clustered_named.pkl")
db['generic_clusters'] = db['cluster_names'].apply(lambda x: x.split(" (")[0])

order_map = {
    'max. PV':1, 
    'PV&hydrogen':2, 
    'wind&battery':3, 
    'max. wind':4,
}

db['sort'] = db['generic_clusters'].apply(lambda x: order_map[x])

#%% plots
plt.tight_layout(pad=PAD)

rc = {
    "font.family": "Open Sans",
    "font.size": 8,
}

plt.rcParams.update(rc)

for scenario in db['scenario'].unique():

    df = db.query(f"scenario == '{scenario}'").copy()
    df.sort_values("sort",inplace=True)
    sdf = df[[*costs, 'cluster_names']]


    g = sns.pairplot(sdf, hue='cluster_names', palette=palette, plot_kws={"size": 10})

    g._legend_data.pop("10")

    handles = g._legend_data.values()
    labels = g._legend_data.keys()
    g._legend.remove()

    g.fig.legend(
        bbox_to_anchor=(0.5, -0.1),
        handles=handles,
        labels=labels,
        loc="lower center",
        frameon=True,
        title="clusters",
        ncol=4,
    )

    plt.subplots_adjust(bottom=0.1)
    g.fig.set_size_inches(6, 5)
    plt.savefig(
        IMAGE_FOLDER / f"report_{COLLECTION}_pairplot_{scenario}.png",
        dpi=300,
        bbox_inches="tight",
    )



