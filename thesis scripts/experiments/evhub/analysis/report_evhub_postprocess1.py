# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt


from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from evhub_postprocess_tools import (
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

#%% load in results
db = get_data_from_db(
    collection=COLLECTION,
    run_id=RUN_ID,
    force_refresh=False
)

#%% plotting
grid_capacities = [0.0, 0.5, 1.0, 1.5]
for grid_cap in grid_capacities:
    ## data selection

    df = db.query(f"grid_capacity == {grid_cap}").copy(deep=True)

    #%% PV Deployment vs absolut cost scatter

    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(6, 2.2)
    sns.scatterplot(
        x="pv_cost_absolute",
        y=pv_col,
        size="total_installed_capacity",
        hue="total_installed_capacity",
        data=df,
        palette="Blues",
        ax=ax,
        edgecolor="black",
    )

    ax.set_ylabel("deployed PV \n capacity (MWp)")
    # ax.set_ylim([-1, 20])

    ax.set_xlabel("PV capacity cost (€/kWp)")
    ax.set_xlim([380, 870])

    l = ax.legend(
        bbox_to_anchor=(1.02, 0.5),
        loc=6,
        borderaxespad=0.0,
        frameon=True,
        title="wind+PV\ncapacity (MW)",
    )
    plt.setp(l.get_title(), multialignment="center")

    default_matplotlib_save(
        fig, IMAGE_FOLDER / f"report_evhub_grid-{grid_cap}_pv_deployment_vs_cost.png", adjust_left=LEFT_MARGIN
    )

    #%% Battery deployment vs absolut cost scatter

    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(6, 2.2)
    sns.scatterplot(
        x="battery_power_cost_absolute",
        y=total_bat_col,
        size="total_installed_capacity",
        hue="total_installed_capacity",
        data=df,
        palette="Blues",
        ax=ax,
        edgecolor="black",
    )

    ax.set_ylabel("deployed battery \n capacity (MWh)")
    # ax.set_ylim([-1, 20])

    ax.set_xlabel("battery power capacity cost (€/kW)")
    # ax.set_xlim([100, 180])

    l = ax.legend(
        bbox_to_anchor=(1.02, 0.5),
        loc=6,
        borderaxespad=0.0,
        frameon=True,
        title="wind+PV\ncapacity (MW)",
    )
    plt.setp(l.get_title(), multialignment="center")

    default_matplotlib_save(
        fig,
        IMAGE_FOLDER / f"report_evhub_grid-{grid_cap}_battery_deployment_vs_cost.png",
        adjust_left=LEFT_MARGIN,
    )

    #%% Wind deployment vs absolut cost scatter

    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(6, 2.2)
    sns.scatterplot(
        x="wind_cost_absolute",
        y=wind_col,
        size="total_installed_capacity",
        hue="total_installed_capacity",
        data=df,
        palette="Blues",
        ax=ax,
        edgecolor="black",
    )

    ax.set_ylabel("deployed wind \n capacity (MW)")
    # ax.set_ylim([-1, 20])

    ax.set_xlabel("wind capacity cost (€/kW)")
    # ax.set_xlim([380, 870])

    l = ax.legend(
        bbox_to_anchor=(1.02, 0.5),
        loc=6,
        borderaxespad=0.0,
        frameon=True,
        title="wind+PV\ncapacity (MW)",
    )
    plt.setp(l.get_title(), multialignment="center")

    default_matplotlib_save(
        fig, IMAGE_FOLDER / f"report_evhub_grid-{grid_cap}_wind_deployment_vs_cost.png"
    )

    #%% relative curtailment
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(3, 3)

    sns.scatterplot(
        x="total_installed_capacity",
        y="relative_curtailment",
        hue=total_bat_col,
        data=df,
        palette="Blues",
        ax=ax,
        edgecolor="black",
    )

    ax.set_xlabel("total deployed capacity (MW)")
    # ax.set_xlim([0, 40])

    ax.set_ylabel("relative curtailment (%)")
    # ax.set_ylim([0, 6])

    ax.legend(
        bbox_to_anchor=(0.5, -0.35),
        loc=9,
        borderaxespad=0.0,
        frameon=True,
        title="deployed battery capacity (MWh)",
        ncol=3,
    )

    default_matplotlib_save(
        fig, IMAGE_FOLDER / f"report_evhub_grid-{grid_cap}_curtailment_vs_deployment.png"
    )

    #%% absolute curtailment
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(3, 3)

    sns.scatterplot(
        x="total_installed_capacity",
        y="curtailment",
        hue=total_bat_col,
        data=df,
        palette="Blues",
        ax=ax,
        edgecolor="black",
    )

    ax.set_xlabel("total deployed capacity (MW)")
    # ax.set_xlim([0, 40])

    ax.set_ylabel("curtailment (MWh)")
    # ax.set_ylim([0, 3000])

    ax.legend(
        bbox_to_anchor=(0.5, -0.35),
        loc=9,
        borderaxespad=0.0,
        frameon=True,
        title="deployed battery capacity (MWh)",
        ncol=3,
    )

    default_matplotlib_save(
        fig,
        IMAGE_FOLDER / f"report_evhub_grid-{grid_cap}_abs_curtailment_vs_deployment.png",
    )


    ###
    for tech, tech_col in bivar_tech_dict.items():
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
            hue=tech_col,
            data=df,
            palette="Blues",
            sizes=(10, 80),
            ax=ax,
            edgecolor="black",
        )

        ax.set_ylabel("battery power\ncapacity cost (€/kW)")
        # ax.set_ylim([100, 180])

        ax.set_xlabel("PV capacity cost (€/kWp)")
        # ax.set_xlim([370, 870])
        ax.legend(
            bbox_to_anchor=(0.5, -0.4),
            loc=9,
            borderaxespad=0.0,
            frameon=True,
            title=f"deployed {tech} capacity ({unit})",
            ncol=6,
            handletextpad=0.1,
        )

        default_matplotlib_save(
            fig, IMAGE_FOLDER / f"report_evhub_grid-{grid_cap}_bivariate_pv_vs_bat_{tech}.png"
        )

    
        #%% bi-variate scatterplot WIND vs BAT

        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(5, 3)

        sns.scatterplot(
            x="wind_cost_absolute",
            y="battery_power_cost_absolute",
            size=tech_col,
            hue=tech_col,
            data=df,
            palette="Blues",
            sizes=(10, 80),
            ax=ax,
            edgecolor="black",
        )

        ax.set_ylabel("battery power\ncapacity cost (€/kW)")
        # ax.set_ylim([160, 310])

        ax.set_xlabel("wind capacity cost (€/kW)")
        # ax.set_xlim([370, 870])
        ax.legend(
            bbox_to_anchor=(0.5, -0.4), 
            loc=9,
            borderaxespad=0.0,
            frameon=True,
            title=f"deployed {tech} capacity ({unit})",
            ncol=6,
            handletextpad=0.1,
        )

        default_matplotlib_save(
            fig,
            IMAGE_FOLDER
            / f"report_evhub_grid-{grid_cap}_bivariate_wind_vs_bat_{tech}.png",
        )

        #%% bi-variate scatterplot WIND vs PV

        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(5, 3)

        sns.scatterplot(
            x="wind_cost_absolute",
            y="pv_cost_absolute",
            size=tech_col,
            hue=tech_col,
            data=df,
            palette="Blues",
            sizes=(10, 80),
            ax=ax,
            edgecolor="black",
        )

        ax.set_ylabel("PV capacity\ncost (€/kWp)")
        # ax.set_ylim([160, 310])

        ax.set_xlabel("wind capacity cost (€/kW)")
        # ax.set_xlim([370, 870])
        ax.legend(
            bbox_to_anchor=(0.5, -0.4),
            loc=9,
            borderaxespad=0.0,
            frameon=True,
            title=f"deployed {tech} capacity ({unit})",
            ncol=6,
            handletextpad=0.1,
        )

        default_matplotlib_save(
            fig,
            IMAGE_FOLDER
            / f"report_evhub_grid-{grid_cap}_bivariate_wind_vs_pv_{tech}.png",
        )
