from LESO import ETMdemand
from LESO.defaultvalues import scenarios_res
import pandas as pd

gqueries = [
    "mv_hv_trafo_capacity_present",  # MW
    "total_electricity_consumed",  # MJ
    "electricity_produced_from_wind",  # MJ
    "electricity_produced_from_solar",  # MJ
    "network_to_export1_in_sankey",  # PJ
    "dashboard_share_of_renewable_electricity",  # %
]

user_values = [
    "flh_of_solar_pv_solar_radiation",   # 950 h
    "flh_of_energy_power_wind_turbine_inland",  # 3500 h
]

etm_objects = []
for i, (name, nest) in enumerate(scenarios_res.items()):
    etm_object = ETMdemand(name, nest["id"], end_year=2030)
    for g in gqueries:
        if g not in etm_object.api.gqueries:
            etm_object.api.gqueries.append(g)
            etm_object.api.user_values.update({
                key: None for key in user_values
            })

    etm_object.api.update_metrics()
    etm_object.api.get_user_values()
    etm_objects.append(etm_object)


#%%

dicto = {}
for etmd in etm_objects:
    dicto.update(
        {
            etmd.name.replace("2030RES_", ""): {
                query: etmd.api.metrics.future[query] for query in gqueries
            }
        }
    )


df = pd.DataFrame.from_dict(dicto, orient="index")
df.iloc[:, 1:4] = df.iloc[:, 1:4] /1e9

df.to_clipboard()



# %%
