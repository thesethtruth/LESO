import numpy as np
import LESO
from LESO.optimizer.extension import constrain_minimal_share_of_renewables, contexted_constraint
from gld2030_definitions import scenarios_2030, MODELS

SCENARIO = list(scenarios_2030.keys())[0]

scenario_data = scenarios_2030[SCENARIO]
STRATEGIES = {
    "no_target": (None, None),
    "current_projection_include_export": (scenario_data['target_re_share'], False),
    "current_projection_excl_export": (scenario_data['target_re_share_ex_export'], True),
    "fixed_target_60": (.60, True),
    "fixed_target_80": (.80, True),
    "fixed_target_100": (1, True),
}

model_to_open = MODELS[SCENARIO]
target_RE_strategy = "current_projection_excl_export"

system = LESO.System.read_pickle(model_to_open)

target_share, exclude_export_from_share = STRATEGIES[target_RE_strategy]

# grab the ETM demand component
for component in system.components:
    if isinstance(component, LESO.ETMdemand):
        demand = component

# set the correct 
    if target_share:
        re_share_constraint = contexted_constraint(
            constrain_minimal_share_of_renewables,
            share_of_re=target_share,
            demands=[demand],
            exclude_export_from_share=exclude_export_from_share
        )
    else: 
        re_share_constraint = None

## SOLVE
system.optimize(
    objective="osc",  # overnight system cost
    additional_constraints= re_share_constraint,
    store=False,  # write-out to json
    solve=True,  # solve or just create model
    # nonconvex=True,
    tee=True,
)
#%%
if True:

    generators = [LESO.PhotoVoltaic, LESO.PhotoVoltaicAdvanced, LESO.BifacialPhotoVoltaic, LESO.Wind, LESO.WindOffshore]

    storages = [LESO.Lithium, LESO.Hydrogen]
    
    pyo_model = system.model
    time = pyo_model.time
    t_zero, t_final = time[0], time[-1]

    contributing_components = {}

    for component in system.components:

        # catch generators
        is_generator = any(isinstance(component, generator) for generator in generators)
        if is_generator:

            # for this we can just sum the dataframe
            contributing_components.update({
                component.name: sum(component.state.power)
            })

        # catch storages
        is_storage = any(isinstance(component, storage) for storage in storages)
        if is_storage:
            ckey = component.__str__()
            energy = getattr(pyo_model, ckey + "_E", None)

            # if energy is buffered at the end of the year it does not contribute towards the goals; 
            # so it should be substracted from initial state of charge
            contributing_components.update({
                component.name : energy[t_zero] - energy[t_final]
            })

        
        # cath final balance
        if isinstance(component, LESO.FinalBalance):
            ckey = component.__str__()
            curtailment = getattr(pyo_model, ckey + "_Pneg", None)

            # curtailment is negative by deffinition; so we can just add this to the sum
            contributing_components.update({
                component.name : sum(curtailment[t] for t in time)
            })
        
        # catch grid
        if isinstance(component, LESO.Grid):

            ckey = component.__str__()
            importo = getattr(pyo_model, ckey + "_Ppos", None) if exclude_export_from_share else np.zeros(len(time))
            export = getattr(pyo_model, ckey + "_Pneg", None) if exclude_export_from_share else np.zeros(len(time))
            
            
            # export is negative by deffinition; so we can just add this to the sum
            contributing_components.update({
                "export": sum(export[t] for t in time),
                "import": - sum(importo[t] for t in time)
            })

    realized_share = sum(
            component for component in contributing_components.values()
        ) / (
            - sum(demand.state.power.sum() for demand in [demand])
        )
# %%
for c in system.components:
    if getattr(c, "installed", False):
        print(c.name, c.installed)

    if isinstance(c, LESO.Grid):
        ckey = c.__str__()
        export = getattr(pyo_model, ckey + "_Pneg", None)
        grid = c
    if isinstance(c, LESO.Lithium):
        if c.EP_ratio == 2:
            bat = c


print("---")

from pyomo.environ import value
for key, v in contributing_components.items():
    if not isinstance(v, float):
        print(key, value(v)/1e6)
    else:
        print(key, v/1e6)
print("exported:", value(sum(export[t] for t in time))/1e6)

print("---")
print("realized_share:", value(realized_share))
# print("realized_share (no export):", value(realized_share) -  value(sum(export[t] for t in time))/demand.state.power.sum())
print("total_demand:", demand.state.power.sum()/1e6)
# %%

system.to_json("latest.json")

# %%
