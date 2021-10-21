#%%
from pathlib import Path
import numpy as np
import LESO
from LESO.logging import log_to_stderr
from LESO.optimizer.extension import contexted_constraint, constrain_minimal_share_of_renewables
log_to_stderr(level=20)


#%%
FOLDER = Path(__file__).parent
MODEL = FOLDER / 'gelderland_2050_regional.pkl'
exclude_export_from_share=True
share_of_re=1


system = LESO.System.read_pickle(MODEL)
for component in system.components:
    if isinstance(component, LESO.ETMdemand):
        demands = [component]

re_share_constraint = contexted_constraint(
    constrain_minimal_share_of_renewables,
    share_of_re=share_of_re,
    demands=demands,
    exclude_export_from_share=exclude_export_from_share
)

# %%
system.optimize(
    objective="osc",  # overnight system cost
    additional_constraints= re_share_constraint,
    time=None,  # resorts to default; year 8760h
    store=False,  # write-out to json
    solver="gurobi",  # default solver
    nonconvex=False,  # solver option (warning will show if needed)
    solve=True,  # solve or just create model
    tee=True,
    method=None,
)


print(f"Target RE share: {share_of_re}")


#%% alternative

generation = 0
export = 0
curtailment = 0
storage_losses = 0
demand = -demands[0].state.power.sum()

for component in system.components:
    # generation
    if isinstance(component, (LESO.Wind, LESO.PhotoVoltaic)):
        generation += component.state.power.sum()
    # export
    if isinstance(component, LESO.Grid):
        export -= component.state['power [-]'].sum()

    # curtailment
    if isinstance(component, LESO.FinalBalance):
        curtailment -= component.state['power [-]'].sum()

    # storage_losses
    if isinstance(component, LESO.Storage):
        storage_losses += component.state['losses'].sum()

pt_share_of_re = (generation - export - curtailment - storage_losses)/demand


print("")
print(f"Target RE share: {share_of_re}")
print(f"Calculated RE share: {pt_share_of_re}")

# %%

