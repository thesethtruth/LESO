# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from seaborn.miscplot import palplot

from LESO.experiments.analysis import (
    load_ema_leso_results,
    open_leso_experiment_file,
)
from LESO.plotting import default_matplotlib_save, default_matplotlib_style

FOLDER = Path(__file__).parent
EXPERIMENTS_FOLDER = FOLDER / "experiments"
IMAGES_FOLDER = FOLDER / "images"
IMAGES_FOLDER.mkdir(exist_ok=True)
LINEWIDTH = 0.5
OPACITY = 0.6
SUPPLY_COLORS = {
    "PV": "#ebd25b",
    "wind": "#8cc0ed",
    "battery discharging": "#7fc78f",
    "import": "#f2b65c",
}
LOAD_COLORS = {
    "chargers": "#a5c0c2",
    "curtailment": "#454545",
    "battery charging": "#85a0d6",
    "export": "#d18426",
}




def plot_experiment_curves(
    experiment_file: str,
    start: int,
    duration: int,
    fig_filename: str,
    include_only_battery=True,
):
    exp = open_leso_experiment_file(EXPERIMENTS_FOLDER / experiment_file)
    # %%
    dates = pd.date_range(
        "01/01/2030",
        freq="h",
        periods=8760,
    )
    loads = pd.DataFrame(index=dates)
    sources = pd.DataFrame(index=dates)

    components = exp.components
    for ckey in exp.components.keys():

        source = components[ckey].state["power [+]"]
        if sum(source) > 1:
            sources[ckey] = source

        load = components[ckey].state["power [-]"]
        if sum(load) < -1:
            loads[ckey] = load

        try:
            if sum(components[ckey].state["energy"])>1:
                energy = pd.DataFrame(
                    data=components[ckey].state["energy"],
                    index=dates,
                    columns=["battery energy"]
                )
        except KeyError:
            pass
        

    source_matches = {
        "pv": "PV",
        "wind": "wind",
        "lithi": "battery discharging",
        "grid": "import",
    }

    def source_translate(x):
        for key, value in source_matches.items():
            if key in x:
                return value

    sources.columns = [source_translate(col) for col in sources.columns]

    load_matches = {
        "fast": "chargers",
        "lith": "battery charging",
        "Final": "curtailment",
        "grid": "export",
    }

    def load_translate(x):
        for key, value in load_matches.items():
            if key in x:
                return value

    loads.columns = [load_translate(col) for col in loads.columns]

    #%% plotting


    energy = energy.iloc[start : start + duration * 24, :]
    loads = loads.iloc[start : start + duration * 24, :]
    sources = sources.iloc[start : start + duration * 24, :]
    
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(6, 3)

    loads.plot.area(ax=ax, color=LOAD_COLORS, alpha=OPACITY, linewidth=LINEWIDTH)
    sources.plot.area(ax=ax, color=SUPPLY_COLORS, alpha=OPACITY, linewidth=LINEWIDTH)

    limit = 1.1 * sources.sum(axis=1).max()
    ax.set_ylim([-limit, limit])

    plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.0, frameon=False)

    plt.tight_layout(pad=0.3)

    rc = {"font.family": "Open Sans", "font.size": 10, "legend.fontsize": 8}

    plt.rcParams.update(rc)

    ax.set_ylabel("power (MW)")

    default_matplotlib_save(
        fig, IMAGES_FOLDER / f"{fig_filename}_start_{start}_duration{duration}.png"
    )

    if include_only_battery:
        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(6, 3)
        
        charging = loads["battery charging"]
        discharging = sources["battery discharging"]

        energy['p.t. energy balance w/o loss'] = (
            -charging.cumsum()
            - discharging.cumsum()
        ) + energy["battery energy"].iat[0]
        energy['p.t. energy balance w loss'] = (
            energy['p.t. energy balance w/o loss'] + (
            (charging * (1-0.9219544457292888)).cumsum()
            - (discharging * (1.0846522890932808-1)).cumsum()
            - (energy["battery energy"] * (1-0.9995)).cumsum())
        )

        charging.plot.area(
            ax=ax, color=LOAD_COLORS, alpha=OPACITY, linewidth=LINEWIDTH
        )
        discharging.plot.area(
            ax=ax, color=SUPPLY_COLORS, alpha=OPACITY, linewidth=LINEWIDTH
        )
        energy.plot(ax=ax, color=['navy', 'firebrick', 'forestgreen'], style=['--', '--', '--'], linewidth=2*LINEWIDTH)

        

        low_limit = 1.1 * charging.min()
        high_limit = 1.1* max(energy.max())
        
        ax.set_ylim([low_limit, high_limit])

        plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.0, frameon=False)

        plt.tight_layout(pad=0.3)

        rc = {"font.family": "Open Sans", "font.size": 10, "legend.fontsize": 8}

        plt.rcParams.update(rc)

        ax.set_ylabel("power (MW)")

        default_matplotlib_save(
            fig,
            IMAGES_FOLDER
            / f"{fig_filename}_batonly_start_{start}_duration{duration}.png",
        )


def profile_plot_battery(charging: pd.Series, discharging: pd.Series, energy: pd.Series, start: int, duration: int, fig_filename: str):
    fig, ax = plt.subplots()
    fig, ax = default_matplotlib_style(fig, ax)
    fig.set_size_inches(6, 3)
    
    energy = pd.DataFrame(
        data=energy.iloc[start : start + duration * 24].values, 
        index=energy.iloc[start : start + duration * 24].index,
        columns=['battery energy'])
    charging = charging.iloc[start : start + duration * 24]
    discharging = discharging.iloc[start : start + duration * 24]

    charging.name = "battery charging"
    discharging.name = "battery discharging"
    
    energy['p.t. energy balance w/o loss'] = (
        -charging.cumsum()
        - discharging.cumsum()
    ) + energy["battery energy"].iat[0]
    energy['p.t. energy balance w loss'] = (
        energy['p.t. energy balance w/o loss'] + (
        (charging * (1-0.9219544457292888)).cumsum()
        - (discharging * (1.0846522890932808-1)).cumsum()
        - (energy["battery energy"] * (1-0.9995)).cumsum())
    )

    charging.plot.area(
        ax=ax, color=LOAD_COLORS, alpha=OPACITY, linewidth=LINEWIDTH
    )
    discharging.plot.area(
        ax=ax, color=SUPPLY_COLORS, alpha=OPACITY, linewidth=LINEWIDTH
    )
    energy.plot(ax=ax, color=['navy', 'firebrick', 'forestgreen'], style=['--', '--', '--'], linewidth=2*LINEWIDTH)

    

    low_limit = 1.1 * charging.min()
    high_limit = 1.1* max(energy.max())
    
    ax.set_ylim([low_limit, high_limit])

    plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.0, frameon=False)

    plt.tight_layout(pad=0.3)

    rc = {"font.family": "Open Sans", "font.size": 10, "legend.fontsize": 8}

    plt.rcParams.update(rc)

    ax.set_ylabel("power (MW)")

    default_matplotlib_save(
        fig,
        IMAGES_FOLDER
        / f"{fig_filename}_bat_indepth_start_{start}_duration{duration}.png",
    )