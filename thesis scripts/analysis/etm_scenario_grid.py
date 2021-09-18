from LESO import ETMdemand
from LESO.defaultvalues import scenarios_res

gqueries = [
    "mv_hv_trafo_capacity_present",
]

etm_objects = []
for i, (name, nest) in enumerate(scenarios_res.items()):
    etm_oject = ETMdemand(name, nest['id'], end_year=2030)
    for g in gqueries:
        if g not in etm_oject.api.gqueries:
            etm_oject.api.gqueries.append(g)
    
    etm_oject.api.update_metrics()
    etm_objects.append(etm_oject)
    

capacities = {}
share_RE = []
for etmd in etm_objects:
    
    capacity = etmd.api.metrics.present.mv_hv_trafo_capacity_present
    share = etmd.api.metrics.future.dashboard_share_of_renewable_electricity

    capacities.update({etmd.name: capacity})    
    share_RE.append(share)



#%%
import pandas as pd

df = pd.DataFrame.from_dict(capacities, orient='index', columns=['grid_capacity_trafo'])
df['share_of_renewable_electricity'] = share_RE
df.to_clipboard()

# %%
