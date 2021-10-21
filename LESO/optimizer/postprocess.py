# postprocess.py
import pandas as pd
from pyomo.environ import value
from LESO.leso_logging import get_module_logger
import LESO
logger = get_module_logger(__name__)



def process_results(eM, unit='k'):
    
    system = eM
    model = eM.model
    time = eM.time

    unit_map = {
        'None': (1, 'default'),
        'k': (1e3, 'kW(h)'),
        'M': (1e6, 'MW(h)'),
        'G': (1e9, 'GW(h)'),
    }

    # Writing results to system components
    for component in system.components:
        
        # extract power curves send to component
        df = component.state
        
        if hasattr(component, 'power_control'):
            for key, modelvar in component.keylist:
                df[key] = [modelvar[t].value for t in time]
        
            if isinstance(component, LESO.Storage):
                leaked_charge = df["power [-]"][df["power [+]"]!=0].sum() # where one is not 0, the other should be zero.
                component.reflux = leaked_charge # store to component as attribute, so it can be accessed easily later on
                if leaked_charge >= 0.1:
                    logger.warning(f"optimizer post: {component.name} might have simultaneous charge/discharge: {leaked_charge} units")
                else:
                    logger.debug(f"optimizer post: {component.name} does not seem to have battery reflux ({leaked_charge} units)")
        else:

            values = component.state.power[time]
            column = 'power'

            if component.dof:
                key = component.__str__()
                modelvar = getattr(model, key+'_size').value
                df[column] = values * modelvar
            
            else:

                df[column] = values
        
        # extract sizing and attach to component
        if component.dof:
            key = component.__str__()
            _varkey = '_size'
            component.installed = getattr(model, key+_varkey).value
            
            if getattr(model, key+_varkey).value > 1e-5: # TODO remove hard-coded tollerance
                component.installed = getattr(model, key+_varkey).value

            else:
                component.installed = 0

    df = pd.DataFrame(columns=['name','value'])
    non_zeros_components = [c for c in system.components if getattr(c, 'installed', 0) != 0]
    
    names, values = list(), list()
    for i, component in enumerate(non_zeros_components):   
        names.append(component.name)
        values.append(component.installed)

    system.cost = value(model.objective)
    names.append('Objective result')
    values.append(system.cost)
    df['name'] = names
    df['value'] = values
    logger.info("Optimisation result:\n"+df.to_string())
    
    system.optimization_result = {
        "Component name": [
            component.name 
            for component in system.components
            if hasattr(component, 'installed')],
        "Installed capacity": [
            round(component.installed, 2)
            for component in system.components
            if hasattr(component, 'installed')
            ],
        "Unit": [
            unit_map[unit][1]
            for component in system.components
            if hasattr(component, 'installed')
        ]
    }
