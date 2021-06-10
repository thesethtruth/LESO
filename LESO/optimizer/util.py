from LESO.finance import functionmapper
import pyomo.environ as pyo
import numpy as np
import LESO

def battery_control_constraints(model, component):

    key = component.__str__()
    time = model.time

    contraintlist = getattr(model, model.constraint_ID)

    # Fetch states
    E = getattr(model, key+'_E')
    P = getattr(model, key+'_P')
    Ppos = getattr(model, key+'_Ppos')
    Pneg = getattr(model, key+'_Pneg')
    
    # Fetch model variables
    EP_ratio = component.EP_ratio
    # if not DOF just take 1 
    battery_size = getattr(model, key+'_size', 1)
    # if DOF is 1 otherwise scales
    battery_installed = component.installed
    

    # Initial battery soc
    contraintlist.add(
        E[0] == component.startingSOC * battery_size * battery_installed
        )

    # Charging battery
    for t in time:
        if t == time[-1]:
            pass
        else:
            contraintlist.add(
                E[t+1] == E[t]*component.discharge_rate\
                - Ppos[t]/component.cycle_efficieny**0.5\
                + Pneg[t]*component.cycle_efficieny**0.5\
                )

    # Time variable constraints
    for t in time:
        
        # battery energy should be positive
        contraintlist.add(0 <= E[t])
        
        # limit the battery energy state to maximum of size
        contraintlist.add(E[t] <= battery_size * battery_installed)
        
        # limit battery DISCHARGING to bat size
        contraintlist.add(P[t] <= 1/ EP_ratio * battery_size * battery_installed)
        
        # limit battery CHARGING to bat size
        contraintlist.add(P[t] >= -1/ EP_ratio * battery_size * battery_installed)
        
        # Make total power the sum of positive and negative instances of powercurve
        contraintlist.add(P[t] == Ppos[t] + Pneg[t])


def final_balance_power_control_constraints(model, component):

    key = component.__str__()
    time = model.time

    contraintlist = getattr(model, model.constraint_ID)

    zeros = np.zeros(len(time))

    # Fetch states (zeros for non-exisiting modes)
    P = getattr(model, key+'_P', zeros)
    Ppos = getattr(model, key+'_Ppos', zeros)
    Pneg = getattr(model, key+'_Pneg', zeros)

    # Time variable constraints
    for t in time:
        # limit underload
        contraintlist.add(P[t] <= component.positive * component.upper)
        
        # limit curtailment
        contraintlist.add(P[t] >= component.negative * component.lower)
        
        # Make total power the sum of positive and negative instances of powercurve
        contraintlist.add(P[t] == Ppos[t] + Pneg[t])

def direct_power_control_constraints(model, component):

    key = component.__str__()
    time = model.time

    contraintlist = getattr(model, model.constraint_ID)

    zeros = np.zeros(len(time))

    # Fetch states (zeros for non-exisiting modes)
    P = getattr(model, key+'_P', zeros)
    Ppos = getattr(model, key+'_Ppos', zeros)
    Pneg = getattr(model, key+'_Pneg', zeros)

    # make sure the DOF limits don't interfere with non DOF power control
    if not component.dof:
        component.upper = 1
        component.lower = -1

    # Time variable constraints
    for t in time:
        # limit to max import cap
        contraintlist.add(P[t] <= component.positive * component.upper * component.installed)
        # limit to max export cap
        contraintlist.add(P[t] >= component.negative * component.lower * component.installed)
        
        # Make total power the sum of positive and negative instances of powercurve
        contraintlist.add(P[t] == Ppos[t] + Pneg[t])

# Power function for power balance
def power(model, component, t):
    
    key = component.__str__()
    size = component.pyoVar # returns 1 or pyo.Var()
    
    # dispatchable power --> always pyo.IndexVar()
    if hasattr(component, 'power_control'):
        
        power = getattr(model, key+'_P')
        
        ppower = power[t]

    # all other components are either scaled by 1 or pyo.Var()
    else:
        ppower = size*\
                    component.state.power[t]

    return ppower

def set_objective(eM, objective):
    # energyModel = eM
    # objective is the sort of objective capital cost, tco, lcoe
    # functionmapper is a dict-switch
    
    objective = objective.lower()
    objective = functionmapper(objective)

    eM.model.objective = pyo.Objective(
                            expr=sum(
                                objective(component, eM) 
                                for component in eM.components
                                ),
                            sense=pyo.minimize
    )
    pass





###-----------------------------------|| unused ||-------------------------------------###
def capital_cost(model, component):

    key = component.__str__()
    
    time = model.time
    lifetime = getattr(component, 'lifetime', 1)
    
    if component.dof:

        size = getattr(model, key+'_size')
        cost = component.capex/lifetime * size

    elif hasattr(component, 'installed') and hasattr(component, 'cost'):
        cost = component.capex/lifetime * component.installed
    
    else:

        cost = 0

    if isinstance(component, LESO.Grid):
        exportp = getattr(model, key+'_Pneg')
        importp = getattr(model, key+'_Ppos')

        cost = sum(exportp[t] * component.variable_income +\
                    importp[t] * component.variable_cost for t in time)

    if isinstance(component, LESO.Lithium):

        P = getattr(model, key+'_P')
        cost += sum((P[t])**2*component.variable_cost for t in time)

    return cost