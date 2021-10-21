#%%

from pathlib import Path
import LESO
from LESO import Lithium, Hydrogen, System
import pandas as pd

lat, lon = (52.06, 5.93)
system = System(
    lat=lat, 
    lon=lon, 
    model_name="test",
    equity_share=0.2)

# storage
h2_seasonal = Hydrogen("H2 seasonal", dof=True, EP_ratio=700)
h2_subseasonal = Hydrogen("H2 subseasonal", dof=True, EP_ratio=350)

system.add_components([
    h2_subseasonal,
    h2_seasonal,
])


# %%
# get battery component

dicto = {}
for component in system.components:
    component.capex_storage = 37e-3
    dicto.update({
        component.name + " original": {
            "crf": component.crf,
            "capex": component.capex,
            "opex": component.opex,
            "annual cost" : component.crf * component.capex + component.opex
        }
    })


for component in system.components:
    component.capex_storage = 31e-3
    dicto.update({
        component.name + " updated cost": {
            "crf": component.crf,
            "capex": component.capex,
            "opex": component.opex,
            "annual cost" : component.crf * component.capex + component.opex
        }
    })

for component in system.components:
    component.capex_storage = 31e-3
    opex = component.capex_power / component.EP_ratio * component.opex_ratio
    dicto.update({
        component.name + " updated cost + calculation": {
            "crf": component.crf,
            "capex": component.capex,
            "opex": opex,
            "annual cost" : component.crf * component.capex + opex
        }
    })
    


#%%
df = pd.DataFrame.from_dict(dicto)
df.to_clipboard()