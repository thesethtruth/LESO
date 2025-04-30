# test.py

# a list of attributes a component should have for sure
basic = [
    'merit_tag',
    'styling',
    'dof',
    'lower',
    'upper',
    'lifetime',
    'capex',
    'opex',
    'variable_cost',
]

power_control = [
    'positive',
    'negative',
]


def attribute_test(component):
    
    # checking basic attributes
    attrs = list()
    for attr in basic:
        if not hasattr(component, attr):
            attrs.append(attr)
            
    # specifically for dispatchables
    if hasattr(component, 'power_control'):
        for attr in power_control:
            if not hasattr(component, attr):
                attrs.append(attr)

    # financial variable check
    if component.capex == 0:
        if component.lifetime is not None:
            raise ValueError(
                f'Component {component.__str__()} cannot have CAPEX = 0'+
                'whilest lifetime is not none. Either set lifetime to None'+
                'or supply CAPEX != 0.'
            )

    # raise error
    if attrs:
        raise NotImplementedError(
                    f'This component ({component.__str__()}) lacks'+
                    f'these required attributes: {attrs}'
                )
    pass
