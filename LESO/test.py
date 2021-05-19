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
    'variable_income',
    'interest',
    'exp_inflation_rate'
]

power_control = [
    'positive',
    'negative',
]


def attribute_test(component):
    
    attrs = list()
    for attr in basic:
        if not hasattr(component, attr):
            attrs.append(attr)
            

    if hasattr(component, 'power_control'):
        for attr in power_control:
            if not hasattr(component, attr):
                attrs.append(attr)

    if attrs:
        raise NotImplementedError(
                    f'This component ({component.__str__()}) lacks'+
                    f'these required attributes: {attrs}'
                )
    pass
