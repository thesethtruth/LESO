#%%

from pathlib import Path
import LESO

FOLDER = Path(__file__).parent
MODEL = FOLDER / 'evhub.pkl'

system = LESO.System.read_pickle(MODEL)

#%%
system.pyomo_print(time=range(1))

# get battery component
for component in system.components:
    if "2h" in component.name:
        battery = component
# %%

