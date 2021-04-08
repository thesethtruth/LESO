import pyomo.environ as pyo
import LESO
import numpy as np

def init_model(model, system, time):
    for component in system.components:
        
        key = component.__str__()

        # scaling variables
        if component.dof:
            _var = pyo.Var(bounds=(0, component.upper))
            _varkey = '_size'
            setattr(model, key+_varkey, _var)

        # power-control
        if hasattr(component, 'power_control'):
            
            from LESO import Dump
            if getattr(component, 'underload', True):
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

            if getattr(component, 'curtail', True):
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

    # Initialize constraint list
    constraint_ID = 'constraints'
    if not hasattr(model, constraint_ID):
            setattr(model, constraint_ID, pyo.ConstraintList())
    contraintlist = getattr(model, constraint_ID)

    # Fetch states
    E = getattr(model, key+'_E')
    P = getattr(model, key+'_P')
    Ppos = getattr(model, key+'_Ppos')
    Pneg = getattr(model, key+'_Pneg')
    
    # Fetch model variables
    EP_ratio = component.EP_ratio
    battery_size = getattr(model, key+'_size')
    

    # Initial battery soc
    contraintlist.add(
        E[0] == component.startingSOC * battery_size
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
        contraintlist.add(E[t] <= battery_size)
        
        # limit battery DISCHARGING to bat size
        contraintlist.add(P[t] <= 1/ EP_ratio * battery_size)
        
        # limit battery CHARGING to bat size
        contraintlist.add(P[t] >= -1/ EP_ratio * battery_size)
        
        # Make total power the sum of positive and negative instances of powercurve
        contraintlist.add(P[t] == Ppos[t] + Pneg[t])
    
    
    # model.constraint_counter += 1

def dump_control_constraints(model, component):

    key = component.__str__()
    time = model.time

    # Initialize constraint list
    constraint_ID = 'constraints'
    if not hasattr(model, constraint_ID):
            setattr(model, constraint_ID, pyo.ConstraintList())
    contraintlist = getattr(model, constraint_ID)

    zeros = np.zeros(len(time))

    # Fetch states (zeros for non-exisiting)
    P = getattr(model, key+'_P', zeros)
    Ppos = getattr(model, key+'_Ppos', zeros)
    Pneg = getattr(model, key+'_Pneg', zeros)

    # Time variable constraints
    for t in time:
        # limit underload
        contraintlist.add(P[t] <= component.underload * component.upper)
        
        # limit curtailment
        contraintlist.add(P[t] >= component.curtail * component.lower)
        
        # Make total power the sum of positive and negative instances of powercurve
        contraintlist.add(P[t] == Ppos[t] + Pneg[t])
    
    
    # model.constraint_counter += 1

def capital_cost(model, component):

    key = component.__str__()
    
    time = model.time

    if component.dof:

        size = getattr(model, key+'_size')
        cost = component.cost * size

        if hasattr(component, 'power_control'):
            
            # currently empty
            pass

            if isinstance(component, LESO.Lithium):

                P = getattr(model, key+'_P')
                cost += sum((P[t])**2*component.cost/1e8 for t in time)
    elif hasattr(component, 'installed') and hasattr(component, 'cost'):

        cost = component.cost * component.installed
    
    else:

        cost = 0

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






