#%%

from pathlib import Path
import LESO


MODEL_FOLDER = Path(__file__).parent.parent / "model"
RESULTS_FOLDER = Path(__file__).parent.parent / "results"
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

MODEL = MODEL_FOLDER / 'evhub.pkl'

system = LESO.System.read_pickle(MODEL)

# for component in system.components:
#     if "2h" in component.name:
#         component.installed = 20


system.pyomo_print(time=range(3))


#%%
import matplotlib.pyplot as plt
self_discharge = 0.9995
lst = []
for i in range(168):
    if i == 0 :
        lst.append(100)
    else:
        lst.append(
            lst[i-1]*self_discharge
        )

plt.plot(lst)
# %%
