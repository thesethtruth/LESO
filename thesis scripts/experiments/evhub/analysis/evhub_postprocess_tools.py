#%% evhub_postprocess_tools.py
from pathlib import Path
from LESO.experiments.analysis import gdatastore_results_to_df, gcloud_read_experiment
import pandas as pd
import matplotlib.pyplot as plt

FOLDER = Path(__file__).parent
RESOURCE_FOLDER = FOLDER / "resources"
RESOURCE_FOLDER.mkdir(exist_ok=True)

## pointers
pv_col = "PV South installed capacity"
wind_col = "Nordex N100 2500 installed capacity"
bat2_col = "2h battery installed capacity"
bat6_col = "6h battery installed capacity"
bat10_col = "10h battery installed capacity"
total_bat_col = "total_storage_energy"
batcols = [bat2_col, bat6_col, bat10_col]
bivar_tech_dict = {"PV": pv_col, "wind": wind_col, "battery": total_bat_col}


#%% load in results
def get_data_from_db(collection, run_id, force_refresh=False, filter=None):

    filename = f"{collection}_{run_id}.pkl"
    pickled_df = RESOURCE_FOLDER / filename

    # buffer all the calculations/df, only refresh if forced to refresh
    if pickled_df.exists() and not force_refresh:

        print("opened pickle -- not refreshed")
        db = pd.read_pickle(pickled_df)

    else:

        filters = [
            ("run_id", "=", run_id),
        ]
        if filter is not None:
            filters.append(filter)

        db = gdatastore_results_to_df(
            collection=collection,
            filters=filters,
        )
        exp = gcloud_read_experiment(collection, db.filename_export.iat[20])
        ## Hard-coded for convience, can be set to True and recorded in debug
        if False:
            spec_yield_pv = (
                sum(exp.components.pv2.state["power [+]"])
                / exp.components.pv2.settings.installed
            )
            spec_yield_wind = (
                sum(exp.components.wind1.state["power [+]"])
                / exp.components.wind1.settings.installed
            )
        else:
            spec_yield_pv = 1025.3069999999996
            spec_yield_wind = 2937.600000000013

        ## change / add some data
        db["pv_cost_absolute"] = db.pv_cost_factor * 1020
        db["wind_cost_absolute"] = db.wind_cost_factor * 1350
        db["curtailment"] = -db["curtailment"]
        db["total_generation"] = (
            db[pv_col] * spec_yield_pv + spec_yield_wind * db[wind_col]
        )
        db["relative_curtailment"] = db["curtailment"] / db["total_generation"] * 100
        db["total_installed_capacity"] = db[pv_col] + db[wind_col]
        db["total_storage_energy"] = db[batcols].sum(axis=1)
        db["total_storage_power"] = (
            db[bat2_col] / 2 + db[bat6_col] / 6 + db[bat10_col] / 10
        )

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

        ep_ratios = [2, 6, 10]
        for ep_ratio in ep_ratios:
            db[f"battery_cost_absolute_{ep_ratio}h"] = [
                (bcf * storage_ref * ep_ratio + linear_map(bcf) * power_ref) / ep_ratio
                for bcf in db["battery_cost_factor"].values
            ]

        db["battery_power_cost_absolute"] = db["battery_cost_factor"] * power_ref
        print("fetched data from the cloud -- refreshed")
        db.to_pickle(RESOURCE_FOLDER / filename)

    return db


#%%


def add_double_legend(ax, num_clusters, tech, unit):
    h, l = ax.get_legend_handles_labels()
    plt.subplots_adjust(
        hspace=.4,
        bottom=0.4,
    )
    leg1 = ax.legend(
        h[1 : num_clusters + 1],
        l[1 : num_clusters + 1],
        title="clusters",
        bbox_to_anchor=(0.5, -0.63),
        loc=8,
        borderaxespad=0.0,
        frameon=True,
        ncol=6,
        handletextpad=0.1,
    )
    ax.legend(
        h[num_clusters + 2 :],
        l[num_clusters + 2 :],
        title=f"deployed {tech} capacity ({unit})",
        bbox_to_anchor=(0.5, -0.65),
        loc=9,
        borderaxespad=0.0,
        frameon=True,
        ncol=6,
        handletextpad=0.1,
    )

    ax.add_artist(leg1)

