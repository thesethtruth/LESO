#%% evhub_postprocess_tools.py
from pathlib import Path
from LESO.experiments.analysis import (
    gdatastore_results_to_df,
    gcloud_read_experiment
)
import pandas as pd

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
def get_data_from_db(collection, run_id, approach, force_refresh=False, filter=None):

    filename = f"{collection}_{run_id}.{approach}.pkl"
    pickled_db = RESOURCE_FOLDER / filename

    # buffer all the calculations/db, only refresh if forced to refresh
    if pickled_db.exists() and not force_refresh:

        print("opened pickle -- not refreshed")
        db = pd.read_pickle(pickled_db)

    else:
        filters = [
            ("run_id", "=", run_id),
            ("approach", "=", approach)
        ]
        
        if filter is not None:
            filters.append(filter)

        db = gdatastore_results_to_df(
            collection=collection,
            filters=filters
        )

        #%% data selection
        exp = gcloud_read_experiment(
            collection=collection,
            experiment_id=db.filename_export.iat[189]
        )

        # hard code the values for convience
        if False:
            spec_yield_pv = (
                sum(exp.components.pv1.state['power [+]']) /
                exp.components.pv1.settings.installed 
            )
            tot_yield_wind = sum(exp.components.wind1.state['power [+]'])
        else:
            spec_yield_pv = 1038.184000000002
            tot_yield_wind = 28684.25000000016

        ## change / add some data
        db['pv_cost_absolute'] = db.pv_cost_factor * 1020
        db['curtailment'] = -db['curtailment']
        db['total_generation'] = (db[pv_col] * spec_yield_pv + tot_yield_wind)
        db['relative_curtailment'] = db['curtailment'] / db['total_generation'] *100
        db['total_installed_capacity'] = db[pv_col] + 10
        db["total_installed_capacity"] = db[pv_col] + db[wind_col]
        db["total_storage_energy"] = db[batcols].sum(axis=1)
        db["total_storage_power"] = db[bat2_col] / 2 + db[bat6_col] / 6 + db[bat10_col] / 10
        switch = lambda x: "<1" if x < 1 else ">1"
        db["ratio"] = [switch(x) for x in db[pv_col] / 10]

        #%% Add battery cost for 2 hour battery

        def linear_map(value, ):
            min, max = 0.41, 0.70 # @@
            map_min, map_max = 0.42, 0.81 # @@

            frac = (value - min) / (max-min)
            m_value = frac * (map_max-map_min) + map_min

            return m_value

        power_ref = 257
        storage_ref = 277

        db["battery_cost_absolute_2h"] = [
            (bcf * storage_ref * 2 + linear_map(bcf) * power_ref) / 2
            for bcf in db["battery_cost_factor"].values
        ]
        db["battery_power_cost_absolute"] = db["battery_cost_factor"] * power_ref

        print("fetched data from the cloud -- refreshed")
        db.to_pickle(RESOURCE_FOLDER / filename)
    
    return db