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

## maps
col_map = {
    pv_col: "PV",
    wind_col: "wind",
    total_bat_col: "battery",
    total_h2_col: "hydrogen",
}
features = list(col_map.values())
scenarios = {
    "Gelderland_2050_regional": {
        "title": "Regional",
        "clusters": 4,  # maybe 5
        "sort": 1,
    },
    "Gelderland_2050_national": {
        "title": "National",
        "clusters": 4,  # four for sure
        "sort": 2,
    },
    "Gelderland_2050_european": {
        "title": "European",
        "clusters": 4,  # maybe 5
        "sort": 3,
    },
    "Gelderland_2050_international": {
        "title": "International",
        "clusters": 4,  # four for sure
        "sort": 4,
    },
}
cluster_col = "clusters_predef_num_clusters"
scenario_col = "scenario"
pairplot_col_map = {
    "pv_cost_factor": "pv cost factor",
    "wind_cost_factor": "wind cost factor",
    "battery_cost_factor": "battery cost factor",
    "hydrogen_cost_factor": "hydrogen cost factor",
}
#%% fetch and process data
db = pd.read_pickle(RESOURCE_FOLDER / f"{COLLECTION}_2210_v2_clustered.pkl")

## rename columns
db.rename(col_map, inplace=True, axis=1)
db["sort"] = db.scenario.apply(lambda x: scenarios[x]["sort"])
db.sort_values(["sort", cluster_col], inplace=True)
db["scenario"] = db.scenario.apply(lambda x: scenarios[x]["title"])


#%% add new column for the translated columns
scenario_cluster_order = {}
gdb = db.groupby('scenario')
for i,g in gdb:

    scenario = g.scenario.unique()[0]
    scenario_ct_dict = clusters_translation[scenario]


    def translator(x:str):

        cluster = x.split(" ")
        cluster_number = int(cluster[0])
        cluster_end = cluster[1]
        name = cluster_names[scenario_ct_dict[cluster_number]['name']]
        new_name = name +" "+ cluster_end
        return new_name
    
    db.loc[g.index, 'cluster_names'] = g[cluster_col].apply(translator)
    tcols = g[cluster_col].apply(translator).unique()
    
    def orderer(x:str):
        for order, name in cluster_names.items():
            if name in x:
                return order
    
    scenario_cluster_order.update({
        scenario: [x for _,x in sorted(zip([orderer(x) for x in tcols],tcols))]
    })

db.to_pickle(RESOURCE_FOLDER / f"{COLLECTION}_2210_v2_clustered_named.pkl")

#%%
df = db[[*features, cluster_col, 'cluster_names', scenario_col]].copy()
df[features] = df[features] / 1000

palette_d = []
for attribute in scenarios.values():
    pal = palette[: attribute["clusters"]]
    attribute.update({"palette": pal})
    palette_d.extend(pal)



#%%

for fn_scenario, attribute in scenarios.items():
    scenario = attribute["title"]
    sdf = df.query(f"scenario == '{scenario}'").copy()

    sdf['order'] = sdf.cluster_names.apply(lambda x: scenario_cluster_order[scenario].index(x))
    sdf.sort_values('order', inplace=True)

    fig, axi = plt.subplots(
        5, 1, figsize=(6, 5), gridspec_kw={"height_ratios": [*[5] * 4, 1]}
    )
    plt.tight_layout(pad=PAD)
    plt.subplots_adjust(bottom=0.8)
    rc = {
        "font.family": "Open Sans",
        "font.size": 10,
        "legend.fontsize": 8,
    }
    plt.rcParams.update(rc)
    plt.subplots_adjust(hspace=0.1)
    for ax in axi.flat:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

    axs = axi.flat

    
    for i, (feature) in enumerate(features):

        ax = axs[i]

        if "battery" in feature or "hydrogen" in feature:
            unit = "GWh"
        else:
            unit = "GW"
        sns.stripplot(
            x=feature,
            y='cluster_names',
            data=sdf,
            hue='cluster_names',
            hue_order=scenario_cluster_order[scenario],
            ax=ax,
            orient="h",
            size=2,
            alpha=1,
            jitter=0.45,
            palette=attribute["palette"],
        )

        
        ax.get_legend().remove()
        ax.set_ylabel("")
        ax.set_yticklabels([])
        ax.set_xlabel(f"{feature} deployed capacity ({unit})")
        ax.set_xlim([-0.3, sdf.max()[feature] if sdf.max()[feature] > 15 else 15])

        ax.tick_params(
            axis="both",
            which="both",
            left=False,
            labelleft=False,
        )
        
    axi[-1].axis("off")
    axi[-1].legend(
        handles=[
            Patch(facecolor=c, edgecolor=c, label=label)
            for c, label in zip(palette, scenario_cluster_order[scenario])
        ],
        frameon=True,
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        loc="upper center",
        title="clusters",
    )

    default_matplotlib_save(
        fig,
        IMAGE_FOLDER / f"report_{COLLECTION}_striplot_translated_clusters_{fn_scenario}.png",
    )
#%% strip plot of all scenarios

df['generic_clusters'] = df['cluster_names'].apply(lambda x: x.split(" (")[0])
hue_order = [x.split(" (")[0] for x in scenario_cluster_order[scenario]]



fig, axi = plt.subplots(4, 1, figsize=(6, 8))
plt.tight_layout(pad=PAD)
rc = {
    "font.family": "Open Sans",
    "font.size": 10,
    "legend.fontsize": 8,
}
plt.rcParams.update(rc)
plt.subplots_adjust(hspace=0.1)
for ax in axi.flat:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

axs = axi.flat
for i, (feature) in enumerate(features):
    ax = axs[i]

    if "battery" in feature or "hydrogen" in feature:
        unit = "GWh"
    else:
        unit = "GW"

    sns.stripplot(
        x=feature,
        y=scenario_col,
        data=df,
        hue='generic_clusters',
        hue_order=hue_order,
        ax=ax,
        orient="h",
        size=2,
        alpha=1,
        jitter=0.45,
        palette=palette_d,
    )

    ax.get_legend().remove()
    ax.set_ylabel("")
    ax.set_xlabel(f"{feature} deployed capacity ({unit})")


axi[0].legend(
    handles=[Patch(facecolor=c, edgecolor=c, label=label) for c, label in zip(palette, hue_order)],
    frameon=False,
    ncol=1,
    loc="upper right",
    title="clusters",
)

default_matplotlib_save(
    fig,
    IMAGE_FOLDER / f"report_{COLLECTION}_striplot_translated_clusters_all_scenarios.png",
)

#%% Facet plot

df['order'] = df.generic_clusters.apply(lambda x: hue_order.index(x))
df.sort_values('order', inplace=True)


for feature in features:

    if "battery" in feature or "hydrogen" in feature:
        unit = "GWh"
    else:
        unit = "GW"

    g = sns.FacetGrid(
        df, row="scenario", hue='generic_clusters', hue_order=hue_order, aspect=15, height=1, palette=palette
    )
    rc = {
        "font.family": "Open Sans",
        "font.size": 10,
    }

    plt.rcParams.update(rc)
    # for cluster in sdf[cluster_col].unique():
    g.map(sns.kdeplot, feature, clip_on=False, color="w", lw=4, bw_adjust=0.5)
    g.map(
        sns.kdeplot, feature, bw_adjust=0.5, clip_on=False, fill=True, alpha=0.7, linewidth=1.5
    )

    g.despine(bottom=False, left=True)
    scenarios_ = df.scenario.unique()
    for i, ax in enumerate(g.axes.flat):
        lvl = -i * 10
        artists = ax.get_children()
        
        if ax is not g.axes.flat[-1]:
            ax.spines["bottom"].set_visible(False)
            ax.tick_params(
                axis="both",
                which="both",
                left=False,
                bottom=False,
                labelleft=True,
            )
        else:
            ax.set_xlabel(f"{feature} deployed capacity ({unit})")

        ax.set_ylabel(scenarios_[i], rotation=0, ha='right', va="top")
        

        for artist in artists:

            if isinstance(artist, Line2D):
                artist.set_zorder(lvl - 2 )
            if isinstance(artist, PolyCollection):
                artist.set_zorder(lvl)

    # Set the subplots to overlap
    g.fig.subplots_adjust(hspace=-0.4)


    # Remove axes details that don't play well with overlap
    g.set_titles("")
    g.set(yticks=[])

    g.fig.set_size_inches(6, 2)
    plt.tight_layout(pad=PAD)

    plt.savefig(
        IMAGE_FOLDER / f"report_{COLLECTION}_facetgrid_translated_clusters_all_scenarios_{feature}.png", dpi=300
    )

# %%
if input("Crop the images in this folder? [y/n]") == "y":
    from LESO.plotting import crop_transparency_top_bottom

    crop_transparency_top_bottom(
        folder_to_crop=IMAGE_FOLDER, file_ext_to_crop="png", override_original=True, crop_top=True
    )
#%% Stack the facet grid

# create legend
fig, ax = plt.subplots(1, 1, figsize=(6, 0.6))
plt.tight_layout(pad=PAD)
rc = {
    "font.family": "Open Sans",
    "font.size": 10,
    "legend.fontsize": 8,
}
plt.rcParams.update(rc)
ax.axis("off")
ax.legend(
    handles=[Patch(facecolor=c, edgecolor=c, label=label) for c, label in zip(palette, hue_order)],
    frameon=True,
    ncol=4,
    bbox_to_anchor=(0.5, -0.1),
    loc="upper center",
    title="clusters",
)
plt.tight_layout(pad=PAD)
plt.subplots_adjust(left=0.15)
plt.savefig(
    IMAGE_FOLDER / f"facetgrid_legend.png", dpi=300
)

#%%


from PIL import Image
paths = list(IMAGE_FOLDER.glob(f"report_{COLLECTION}_facetgrid_translated_clusters_all_scenarios*"))
paths = [p for p in paths if "stacked" not in str(p)]
order = [features.index(f) for f in features]
order = [x for _,x in sorted(zip([f.lower() for f in features], order))]

sorted_paths = [x for _,x in sorted(zip(order, paths))]
sorted_paths.append(next(IMAGE_FOLDER.glob("facetgrid_legend*")))
ims = [Image.open(p) for p in sorted_paths]
im = Image.fromarray(np.vstack(ims))

im.save(IMAGE_FOLDER / f"report_{COLLECTION}_facetgrid_translated_clusters_all_scenarios_stacked.png")


#%%
