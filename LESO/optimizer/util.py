import pyomo.environ as pyo
import numpy as np
import LESO

def init_model(system, model, time):

    # Initialize constraint list
    constraint_ID = model.constraint_ID
    if not hasattr(model, constraint_ID):
            setattr(model, constraint_ID, pyo.ConstraintList())

    for component in system.components:
        
        key = component.__str__()

        # scaling variables
        if component.dof:
            _var = pyo.Var(bounds=(0, component.upper))
            _varkey = '_size'
            setattr(model, key+_varkey, _var)

        # power-control
        if hasattr(component, 'power_control'):
            
            if getattr(component, 'positive', True):
                # positive-only part of power
                _varkey = '_Ppos'
                setattr(
                    model, 
                    key+_varkey, 
                    pyo.Var(
                        time, 
                        domain = pyo.NonNegativeReals, 
                        initialize = 0
                        ))
                _key_setter(model, _varkey, key, component)

            if getattr(component, 'negative', True):
                # negative-only part of power
                _varkey = '_Pneg'
                setattr(
                    model, 
                    key+_varkey, 
                    pyo.Var(
                        time, 
                        domain = pyo.NonPositiveReals, 
                        initialize = 0
                        ))
                _key_setter(model, _varkey, key, component)

            # power total
            _varkey = '_P'
            setattr(
                model, 
                key+_varkey, 
                pyo.Var(
                    time,
                    ))
            _key_setter(model, _varkey, key, component)

        from LESO import Storage
        if isinstance(component, Storage):
            # Energy
            _varkey = '_E'
            setattr(
                model, 
                key+_varkey, 
                pyo.Var(
                    time,
                    ))
            _key_setter(model, _varkey, key, component)


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
                E[t+1] == E[t] - P[t]
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
    
    if component.dof:
        size = getattr(model, key+'_size')
    

    # power is controlable (battery, grid)
    if hasattr(component, 'power_control'):
        
        power = getattr(model, key+'_P')
        
        ppower = power[t]
            
    # must-meet loads (charger, consumer)
    elif component.merit_tag == 'MM':
        ppower = component.state.power[t] 
    
    # is VRE (wind, pv)
    elif component.merit_tag == 'VRE':
        
        # VRE component is a dof
        if component.dof:
            ppower = size*\
                      component.state.power[t] 
        
        # VRE component is not a dof, use installed capacity
        else:
              ppower = component.installed*\
                      component.state.power[t] 
        
    return ppower


def capital_cost(model, component):

    key = component.__str__()
    
    time = model.time
    lifetime = getattr(component, 'lifetime', 1)
    
    if component.dof:

        size = getattr(model, key+'_size')
        cost = component.cost/lifetime * size

    elif hasattr(component, 'installed') and hasattr(component, 'cost'):
        cost = component.cost/lifetime * component.installed
    
    else:

        cost = 0

    if isinstance(component, LESO.Grid):
        exportp = getattr(model, key+'_Pneg')
        importp = getattr(model, key+'_Ppos')

        cost = sum(exportp[t] * component.price +\
                    importp[t] * component.cost for t in time)

    if isinstance(component, LESO.Lithium):

        P = getattr(model, key+'_P')
        cost += sum((P[t])**2*component.cost/1e8 for t in time)

    return cost




def _key_setter(model, _varkey, key, component):

    mapper = {
        '_P': 'power',
        '_Ppos': 'power [+]',
        '_Pneg': 'power [-]',
        '_E': 'energy',
    }

    _keyname = mapper.get(_varkey, None)
    
    if _keyname is None:
        raise NotImplementedError(f'Key "{_varkey}"does not exist in mapper.') 

    _modelvar = getattr(model, key+_varkey)
    
    _keypair = (_keyname, _modelvar)

    component.keylist.append(_keypair)