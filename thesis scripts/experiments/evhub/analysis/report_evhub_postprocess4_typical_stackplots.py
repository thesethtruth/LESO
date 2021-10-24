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
    bivar_tech_dict,
)

from LESO.defaultvalues import merit_order_dict

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
starts = [300, 2100, 4500, 6400]# hour
duration = 7  # days

db = pd.read_pickle(RESOURCE_FOLDER / "ref_systems_df.pkl")
for _, row in db.iterrows():
    filename = row.filename_export
    grid_cap = row.grid_capacity
    exp = gcloud_read_experiment(collection=COLLECTION, experiment_id=filename)
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
        try:
            source = components[ckey].state["power [+]"]
            if sum(source) > 1:
                sources[ckey] = source
        except KeyError:
            ...

        try:
            load = components[ckey].state["power [-]"]
            if sum(load) < -10:
                loads[ckey] = load
        except KeyError:
            ...

    #%%
    source_matches = {
        "pv": "PV",
        "wind": "wind",
        "lithi": "battery discharging",
        "grid": "import",
    }
    source_order = {
        "PV": "0",
        "wind": "1",
        "battery discharging": "2",
        "import": "3",
    }
    order_source = {value: key for key, value in source_order.items()}

    def source_translate(x):
        for key, value in source_matches.items():
            if key in x:
                return value

    sources.columns = [source_translate(col) for col in sources.columns]
    sources = sources.groupby(sources.columns, axis=1).sum()
    sources.columns = [source_order[col] for col in sources.columns]
    sources = sources.sort_index(axis=1)
    sources.columns = [order_source[col] for col in sources.columns]

    load_matches = {
        "fast": "chargers",
        "lith": "battery charging",
        "Final": "curtailment",
        "grid": "export",
    }
    load_order = {
        "chargers": "0",
        "battery charging": "2",
        "curtailment": "4",
        "export": "3",
    }
    order_load = {value: key for key, value in load_order.items()}

    def load_translate(x):
        for key, value in load_matches.items():
            if key in x:
                return value

    loads.columns = [load_translate(col) for col in loads.columns]
    loads = loads.groupby(loads.columns, axis=1).sum()
    loads.columns = [load_order[col] for col in loads.columns]
    loads = loads.sort_index(axis=1)
    loads.columns = [order_load[col] for col in loads.columns]

    #%% plotting

    supply_colors = {
        "PV": "#ebd25b",
        "wind": "#8cc0ed",
        "battery discharging": "#7fc78f",
        "import": "#f2b65c",
    }

    load_colors = {
        "chargers": "#a5c0c2",
        "curtailment": "#454545",
        "battery charging": "#85a0d6",
        "export": "#d18426",
    }


    for start in starts:
        subset_loads = loads.iloc[start : start + duration * 24, :]
        subset_sources = sources.iloc[start : start + duration * 24, :]

        opacity = 0.6

        fig, ax = plt.subplots()
        fig, ax = default_matplotlib_style(fig, ax)
        fig.set_size_inches(6, 2.2)

        subset_loads.plot.area(ax=ax, color=load_colors, alpha=opacity, linewidth=1)
        subset_sources.plot.area(ax=ax, color=supply_colors, alpha=opacity, linewidth=1)

        lim = 1.1 * max(
            [subset_loads.sum(axis=1).abs().max(), subset_sources.sum(axis=1).max()]
            )
        ax.set_ylim([-lim, lim])

        plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.0, frameon=False)

        plt.tight_layout(pad=0.3)
        rc = {"font.family": "Open Sans", "font.size": 10, "legend.fontsize": 8}
        plt.rcParams.update(rc)

        ax.set_ylabel("power (GW)")

        default_matplotlib_save(
            fig, IMAGE_FOLDER / f"report_evhub_curves_grid_{grid_cap}_start_{start}.png"
    )

# %%
