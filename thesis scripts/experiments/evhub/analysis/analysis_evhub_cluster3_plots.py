#%%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from evhub_postprocess_tools import (
    add_double_legend,
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
)

#%% paths
FOLDER = Path(__file__).parent
RESULT_FOLDER = FOLDER.parent / "results"
IMAGE_FOLDER = FOLDER / "images"
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## constants
LEFT_MARGIN = 0.15
COLLECTION = "evhub"
RUN_ID = "2210_v2"
palette = "mako"
cluster_col = "clusters"

bivar_tech_dict_alt = {
    "PV": "PV capacity (MW)",
    "wind": "wind capacity (MW)",
    "battery": "battery capacity (MWh)",
}


#%% load in results
db = pd.read_pickle(RESOURCE_FOLDER / "evhub_2210_v2_clustered.pkl")
db.rename(
    columns={value: bivar_tech_dict_alt[key] for key, value in bivar_tech_dict.items()},
    inplace=True,
)
db.rename(columns={"clusters_from_gridcap": "clusters"}, inplace=True)


#%% plotting
grid_capacities = [0.0, 0.5, 1.0, 1.5]

for grid_cap in grid_capacities:

    ## data selection
    df = db.query(f"grid_capacity == {grid_cap}").copy(deep=True)
    num_clusters = len(df.clusters.unique())

    for tech, tech_col in bivar_tech_dict_alt.items():
        if tech == "battery":
            unit = "MWh"
        else:
            unit = "MW"

        #%% bi-variate scatterplot PV vs BAT
        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(5, 3)

        sns.scatterplot(
            x="pv_cost_absolute",
            y="battery_power_cost_absolute",
            size=tech_col,
            hue=cluster_col,
            data=df,
            palette="mako",
            sizes=(10, 80),
            ax=ax,
            edgecolor="black",
        )

        ax.set_ylabel("battery power\ncapacity cost (€/kW)")
        ax.set_xlabel("PV capacity cost (€/kWp)")

        add_double_legend(ax, num_clusters, tech, unit)

        default_matplotlib_save(
            fig,
            IMAGE_FOLDER
            / f"report_evhub_grid-{grid_cap}_bivariate_cluster_pv_vs_bat_{tech}.png",
        )

        #%% bi-variate scatterplot WIND vs BAT
        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(5, 3)

        sns.scatterplot(
            x="wind_cost_absolute",
            y="battery_power_cost_absolute",
            size=tech_col,
            hue=cluster_col,
            data=df,
            palette="mako",
            sizes=(10, 80),
            ax=ax,
            edgecolor="black",
        )

        ax.set_ylabel("battery power\ncapacity cost (€/kW)")
        ax.set_xlabel("wind capacity cost (€/kW)")

        add_double_legend(ax, num_clusters, tech, unit)

        default_matplotlib_save(
            fig,
            IMAGE_FOLDER
            / f"report_evhub_grid-{grid_cap}_bivariate_cluster_wind_vs_bat_{tech}.png",
        )

        #%% bi-variate scatterplot WIND vs PV

        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(5, 3)

        sns.scatterplot(
            x="wind_cost_absolute",
            y="pv_cost_absolute",
            size=tech_col,
            hue=cluster_col,
            data=df,
            palette="mako",
            sizes=(10, 80),
            ax=ax,
            edgecolor="black",
        )

        ax.set_ylabel("PV capacity\ncost (€/kWp)")
        ax.set_xlabel("wind capacity cost (€/kW)")

        add_double_legend(ax, num_clusters, tech, unit)

        default_matplotlib_save(
            fig,
            IMAGE_FOLDER
            / f"report_evhub_grid-{grid_cap}_bivariate_cluster_wind_vs_pv_{tech}.png",
        )
# %%
