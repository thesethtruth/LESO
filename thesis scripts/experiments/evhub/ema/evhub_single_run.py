#%%

from pathlib import Path
import LESO


MODEL_FOLDER = Path(__file__).parent.parent / "model"
RESULTS_FOLDER = Path(__file__).parent.parent / "results"
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

MODEL = MODEL_FOLDER / 'evhub.pkl'

system = LESO.System.read_pickle(MODEL)
for component in system.components:
    if "Grid" in component.name:
        component.installed = 0

# %%
system.optimize(
    objective="osc",  # overnight system cost
    time=None,  # resorts to default; year 8760h
    store=False,  # write-out to json
    solver="gurobi",  # default solver
    nonconvex=False,  # solver option (warning will show if needed)
    solve=True,  # solve or just create model
)

# %%
import matplotlib.pyplot as plt

for component in system.components:
    if "2h" in component.name:
        bat = component
        df = component.state
        df.plot()


lst = []
for i in range(8760):
    lst.append(-sum(df.loc[df.index[:i],'power [-]'])-sum(df.loc[df.index[:i],'power [+]']))
df.plot()
df['E check'] = lst

plt.figure()
df.loc[df.index[100:200],:].plot()

losses = sum(df['power [+]'] * (1-0.85** .5)  - df['power [-]'] * (1-0.85** .5)  +  df['energy'] * (1-0.995))
df['total losses'] = losses

plt.figure()
df.plot()

# %%
