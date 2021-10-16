# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

from LESO.experiments.analysis import (
    load_ema_leso_results,
    open_leso_experiment_file,
)
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

#%% constants
FOLDER = Path(__file__).parent
FIG_FOLDER = FOLDER / "images"
RESULT_FOLDER = FOLDER.parent / "results"
LEFT_MARGIN = 0.15

run_id = 210907

#%% load in results
experiments, outcomes, db = load_ema_leso_results(
    run_id=run_id, exp_prefix="evhub", results_folder=RESULT_FOLDER
)

## note that for 21 cases the optimizer did not exit sucessfully. No clue on how to deal with this. --> ignore it is

## pointers
pv_col = "PV South installed capacity"
wind_col = "Nordex N100 2500 installed capacity"
bat_col = "2h battery installed capacity"

bivar_tech_dict = {"PV": pv_col, "wind": wind_col, "battery": bat_col}

grid_capacities = [0.5, 1.0, 0.0, 1.5]
for grid_cap in grid_capacities:
    ## data selection

    df = db.query(f"grid_capacity == {grid_cap}").copy(deep=True)
    exp = open_leso_experiment_file(RESULT_FOLDER / df.filename_export.iat[113])

    ## needed for more kpis
    spec_yield_pv = (
        sum(exp.components.pv2.state["power [+]"])
        / exp.components.pv2.settings.installed
    )
    tot_yield_wind = sum(exp.components.wind1.state["power [+]"])

    ## change / add some data
    df["pv_cost_absolute"] = df.pv_cost_factor * 1020
    df["wind_cost_absolute"] = df.wind_cost_factor * 1350
    df["curtailment"] = -df["curtailment"]
    df["total_generation"] = df[pv_col] * spec_yield_pv + tot_yield_wind
    df["relative_curtailment"] = df["curtailment"] / df["total_generation"] * 100
    df["total_installed_capacity"] = df[pv_col] + df[wind_col]

    def linear_map(
        value,
    ):
        min, max = 0.41, 0.70  # @@
        map_min, map_max = 0.42, 0.81  # @@

        frac = (value - min) / (max - min)
        m_value = frac * (map_max - map_min) + map_min

        return m_value

    power_ref = 257
    storage_ref = 277

    df["battery_cost_absolute_2h"] = [
        (bcf * storage_ref * 2 + linear_map(bcf) * power_ref) / 2
        for bcf in df["battery_cost_factor"].values
    ]

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
        fig, FIG_FOLDER / f"report_evhub_grid-{grid_cap}_pv_deployment_vs_cost.png"
    )

    #%% Battery deployment vs absolut cost scatter

    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(6, 2.2)
    sns.scatterplot(
        x="battery_cost_absolute_2h",
        y=bat_col,
        size="total_installed_capacity",
        hue="total_installed_capacity",
        data=df,
        palette="Blues",
        ax=ax,
        edgecolor="black",
    )

    ax.set_ylabel("deployed battery \n capacity (MW)")
    # ax.set_ylim([-1, 20])

    ax.set_xlabel("battery capacity cost (€/kWh)")
    ax.set_xlim([160, 300])

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
        FIG_FOLDER / f"report_evhub_grid-{grid_cap}_battery_deployment_vs_cost.png",
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
        fig, FIG_FOLDER / f"report_evhub_grid-{grid_cap}_wind_deployment_vs_cost.png"
    )

    #%% relative curtailment
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(3, 3)

    sns.scatterplot(
        x="total_installed_capacity",
        y="relative_curtailment",
        hue=bat_col,
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
        title="deployed battery capacity (MW)",
        ncol=3,
    )

    default_matplotlib_save(
        fig, FIG_FOLDER / f"report_evhub_grid-{grid_cap}_curtailment_vs_deployment.png"
    )

    #%% absolute curtailment
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(3, 3)

    sns.scatterplot(
        x="total_installed_capacity",
        y="curtailment",
        hue=bat_col,
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
        title="deployed battery capacity (MW)",
        ncol=3,
    )

    default_matplotlib_save(
        fig,
        FIG_FOLDER / f"report_evhub_grid-{grid_cap}_abs_curtailment_vs_deployment.png",
    )


    ###
    for tech, tech_col in bivar_tech_dict.items():
        #%% bi-variate scatterplot PV vs BAT

        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(5, 3)

        sns.scatterplot(
            x="pv_cost_absolute",
            y="battery_cost_absolute_2h",
            size=tech_col,
            hue=tech_col,
            data=df,
            palette="Blues",
            sizes=(10, 80),
            ax=ax,
            edgecolor="black",
        )

        ax.set_ylabel("2h battery \n capacity cost (€/kWh)")
        # ax.set_ylim([160, 310])

        ax.set_xlabel("PV capacity cost (€/kWp)")
        # ax.set_xlim([370, 870])
        ax.legend(
            bbox_to_anchor=(0.5, -0.4),
            loc=9,
            borderaxespad=0.0,
            frameon=True,
            title=f"deployed {tech} capacity (MW)",
            ncol=6,
            handletextpad=0.1,
        )

        default_matplotlib_save(
            fig, FIG_FOLDER / f"report_evhub_grid-{grid_cap}_bivariate_pv_vs_bat_{tech}.png"
        )

    
        #%% bi-variate scatterplot WIND vs BAT

        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(5, 3)

        sns.scatterplot(
            x="wind_cost_absolute",
            y="battery_cost_absolute_2h",
            size=tech_col,
            hue=tech_col,
            data=df,
            palette="Blues",
            sizes=(10, 80),
            ax=ax,
            edgecolor="black",
        )

        ax.set_ylabel("2h battery \n capacity cost (€/kWh)")
        # ax.set_ylim([160, 310])

        ax.set_xlabel("wind capacity cost (€/kW)")
        # ax.set_xlim([370, 870])
        ax.legend(
            bbox_to_anchor=(0.5, -0.4), 
            loc=9,
            borderaxespad=0.0,
            frameon=True,
            title=f"deployed {tech} capacity (MW)",
            ncol=6,
            handletextpad=0.1,
        )

        default_matplotlib_save(
            fig,
            FIG_FOLDER
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

        ax.set_ylabel("PV capacity \ncost (€/kWp)")
        # ax.set_ylim([160, 310])

        ax.set_xlabel("wind capacity cost (€/kW)")
        # ax.set_xlim([370, 870])
        ax.legend(
            bbox_to_anchor=(0.5, -0.4),
            loc=9,
            borderaxespad=0.0,
            frameon=True,
            title=f"deployed {tech} capacity (MW)",
            ncol=6,
            handletextpad=0.1,
        )

        default_matplotlib_save(
            fig,
            FIG_FOLDER
            / f"report_evhub_grid-{grid_cap}_bivariate_wind_vs_pv_{tech}.png",
        )
