#%%

from pathlib import Path
import LESO

FOLDER = Path(__file__).parent
MODEL = FOLDER / 'evhub.pkl'

system = LESO.System.read_pickle(MODEL)

#%%


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
