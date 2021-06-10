# postprocess.py

from pyomo.environ import value


def process_results(eM, unit='k'):
    
    model = eM.model
    time = eM.time

    unit_map = {
        'k': (1e3, 'kW(h)'),
        'M': (1e6, 'MW(h)'),
        'G': (1e9, 'GW(h)'),
    }

    # Writing results to system components
    for component in eM.components:
        
        # extract power curves send to component
        df = component.state
        
        if hasattr(component, 'power_control'):
            for key, modelvar in component.keylist:
                df[key] = [modelvar[t].value for t in time]
        
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
            print(f'{key} size                 = ',
                round(component.installed/unit_map[unit][0],1), unit+'W(h)')
            
            
    print()
    print('Total system cost (objective)= ', round(value(model.objective)/unit_map[unit][0],1), unit+'€')
    eM.cost = value(model.objective)
    



    eM.optimization_result = {
        "Component name": [
            component.name 
            for component in eM.components
            if hasattr(component, 'installed')],
        "Installed capacity": [
            round(component.installed / unit_map[unit][0],1)
            for component in eM.components
            if hasattr(component, 'installed')
            ],
        "Unit": [
            unit_map[unit][1]
            for component in eM.components
            if hasattr(component, 'installed')
        ]
    }



## ___ From future (with tupples)
# model = eM.model
# time = eM.time

# unit_map = {
#     'k': (1e3, 'kW(h)'),
#     'M': (1e6, 'MW(h)'),
#     'G': (1e9, 'GW(h)'),
# }

# # Writing results to system components
# for component in eM.components:
    
#     # extract power curves send to component
#     df = component.state
    
#     if hasattr(component, 'power_control'):
#         for key, modelvar in component.keylist:
#             df[key] = [modelvar[t].value for t in time]
    
#     else:

#         values = component.state.power[time]
#         column = 'power'

#         if any([component.dof]):
#                 key = component.__str__()
#                 modelvar = getattr(model, key+'_size').value
#                 df[column] = values * modelvar
        
#         else:

#             df[column] = values
    
#     # extract sizing and attach to component
#     if any([component.dof]):
#         key = component.__str__()

#         if isinstance(component.dof, tuple):
            
#             if all(component.dof):
                
#                 component.installed = (
#                     getattr(model, key+'_E_size').value,
#                     getattr(model, key+'_P_size').value)
#             else:

#                 E_size = getattr(model, key+'_E_size').value
#                 component.installed = (
#                     E_size,
#                     E_size/component.EP_ratio)
                

#             print(f'{key} E size               = ',
#                 round(component.installed[0]/unit_map[unit][0],1), unit+'W(h)')
#             print(f'{key} P size               = ',
#                 round(component.installed[1]/unit_map[unit][0],1), unit+'W(h)')
#         else:
#             _varkey = '_size'
#             component.installed = getattr(model, key+_varkey).value
#             print(f'{key} size                 = ',
#                 round(component.installed/unit_map[unit][0],1), unit+'W(h)')

        

        
        
# print()
# print('Total system cost (objective)= ', round(value(model.objective)/unit_map[unit][0],1), unit+'€')
# eM.cost = value(model.objective)




# eM.optimization_result = {
#     "Component name": [
#         component.name 
#         for component in eM.components
#         if hasattr(component, 'installed')],
#     "Installed capacity": [
#         [
#             round(component.installed / unit_map[unit][0],1)
#             if not isinstance(component.installed, tuple)
#             else (round(component.installed[0] / unit_map[unit][0],1),
#                 round(component.installed[1] / unit_map[unit][0],1))
#         ]
#         for component in eM.components
#         if hasattr(component, 'installed') 
#         ],
#     "Unit": [
#         unit_map[unit][1]
#         for component in eM.components
#         if hasattr(component, 'installed')
#     ]
# }