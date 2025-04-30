# preprocess.py
import pyomo.environ as pyo


def initializeGenericPyomoVariables(component, pM):
    """"
    Arguments:
        component:
            instance of any of the LESO.components

        pM:
            Pyomo model
    
    Constructs generic Pyomo variables. This function should be called whenever the component itself lacks 
    a specific variable constructor function.
    
    """
   
    time = pM.time
    key = component.__str__()

    # scaling variables
    if component.dof:
        _var = pyo.Var(bounds=(0, component.upper))
        _varkey = '_size'
        # set the pyoVar to the model
        setattr(pM, key+_varkey, _var)
        # create a pointer to the var from the respc. component
        setattr(component, 'pyoVar', getattr(pM, key+_varkey)) 

    # power-control
    if hasattr(component, 'power_control'):
        
        if getattr(component, 'positive', True):
            # positive-only part of power
            _varkey = '_Ppos'
            setattr(
                pM, 
                key+_varkey, 
                pyo.Var(
                    time, 
                    domain = pyo.NonNegativeReals, 
                    initialize = 0
                    ))
            _key_setter(pM, _varkey, key, component)

        if getattr(component, 'negative', True):
            # negative-only part of power
            _varkey = '_Pneg'
            setattr(
                pM, 
                key+_varkey, 
                pyo.Var(
                    time, 
                    domain = pyo.NonPositiveReals, 
                    initialize = 0
                    ))
            _key_setter(pM, _varkey, key, component)

        # power total
        _varkey = '_P'
        setattr(
            pM, 
            key+_varkey, 
            pyo.Var(
                time,
                ))
        _key_setter(pM, _varkey, key, component)

    # only if the component has energy
    if "energy" in component.state.columns:
        # Energy
        _varkey = '_E'
        setattr(
            pM, 
            key+_varkey, 
            pyo.Var(
                time,
                ))
        _key_setter(pM, _varkey, key, component)
    
    if "losses" in component.state.columns:
        # Energy
        _varkey = '_Losses'
        setattr(
            pM, 
            key+_varkey, 
            pyo.Var(
                time,
                ))
        _key_setter(pM, _varkey, key, component)


def _key_setter(pM, _varkey, key, component):

    mapper = {
        '_P': 'power',
        '_Ppos': 'power [+]',
        '_Pneg': 'power [-]',
        '_E': 'energy',
        '_Losses' : 'losses',
    }

    _keyname = mapper.get(_varkey, None)
    
    if _keyname is None:
        raise NotImplementedError(f'Key "{_varkey}"does not exist in mapper.') 

    _modelvar = getattr(pM, key+_varkey)
    
    _keypair = (_keyname, _modelvar)

    component.keylist.append(_keypair)