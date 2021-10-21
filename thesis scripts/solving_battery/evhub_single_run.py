#%%
from pathlib import Path
import LESO
from profile_plotting import profile_plot_battery
from LESO.logging import log_to_stderr
from logging import INFO


log_to_stderr(level=0)


FOLDER = Path(__file__).parent
MODEL = FOLDER / 'evhub.pkl'


#%%
system = LESO.System.read_pickle(MODEL)


for i, component in enumerate(system.components):
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
    tee=True,
    method=None,
)

#%%
if True:
    batteries_placed = []
    zero_threshold = 0.1
    for component in system.components:
        if isinstance(component, LESO.Lithium):
            if component.installed > zero_threshold:
                batteries_placed.append(component)

    for battery in batteries_placed:
        time = system.time
        df = battery.state.copy(deep=True)

        if hasattr(battery, 'power_control'):
            for key, modelvar in battery.keylist:
                df[key] = [modelvar[t].value for t in time]

        df2 = profile_plot_battery(
            charging = battery.state['power [-]'],
            discharging = battery.state['power [+]'],
            energy= battery.state['energy'],
            start=300,
            duration=7,
            fig_filename="evhub_00mw_changed_cost_",
            plot_pt_no_loss = False,
            plot_pt_w_loss = False,

        )
        # %%


        charging = battery.state['power [-]']
        discharging = battery.state['power [+]']
        energy =battery.state['energy']

        print("leaked discharge :", discharging[charging!=0].sum())
        print("leaked charge :", charging[discharging!=0].sum())
        print("peak power :", max([-charging.min(), discharging.max()]))
        print("peak power [%]:", max([-charging.min(), discharging.max()])/(battery.installed/battery.EP_ratio))
        print("peak energy:", energy.max())
        print("peak energy [%]:", energy.max()/battery.installed)

    # %%

    for component in system.components:
        if "battery" in component.name:
            print(component.name, f": {component.capex}")

    #%%
    for component in system.components:
        try:
            print(component.name, f": {component.installed}")
        except AttributeError:
            pass