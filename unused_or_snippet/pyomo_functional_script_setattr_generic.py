import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import value
import numpy as np

import LESO

solve = True

# Constants
year = 8760
t_span = year
t_min = 0
upper_limit = 10e6 # == 10 MW

time = list( range ( t_min, t_min + t_span) )


max_MW = 10e6 

# Initiate components to consider
pv = LESO.PhotoVoltaic('Full-south PV', dof = True, upper = max_MW )
wind = LESO.Wind('Wind turbine', dof = True, upper = max_MW)
battery = LESO.Lithium('ESS', dof = True, upper = 10e6, startingSOC = 0.2)
charger = LESO.FastCharger('DC fastcharger')
grid = LESO.Grid('200KVA')
dump = LESO.Dump()

# set system to Utrecht location
system = LESO.System(52, 5)


# load TMY
system.fetch_input_data()

# add components to the system (Model Class)
system.add_components([battery, dump, pv, wind, charger ])

# Issue the command for every component to calculate its feed-in on TMY data
system.calculate_time_series()

# Create model
model = pyo.ConcreteModel()
model.time = time
from pyoutil import init_model
init_model(model, system, time)

# Component level constraints
from pyoutil import battery_control_constraints
from pyoutil import dump_control_constraints

for component in system.components:
    if isinstance(component, LESO.Lithium):
        battery_control_constraints(model, component) 
    if isinstance(component, LESO.Dump):
        dump_control_constraints(model, component)

# Power function for power balance
def power(model, component, t):
    
    key = component.__str__()
    
    if component.dof:
        size = getattr(model, key+'_size')
    

    # power is controlable (battery, grid)
    if hasattr(component, 'power_control'):
        
        power = getattr(model, key+'_P')
        
        # controlable component is a dof
        if component.dof:
            ppower = power[t]
        
        # controlable component is not a dof, use installed capacity
        elif hasattr(component, 'installed'):
              ppower = component.installed*power[t]
        
        elif component.merit_tag == 'Dump':
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

# power balance
for t in time: 
    model.constraints.add( 0 == sum(power(model,component,t) for component in system.components ))


# Capital cost for objective
from pyoutil import capital_cost
model.capitalcost = pyo.Objective(
                    expr = sum(capital_cost(model, component) for component in system.components), 
                    sense = pyo.minimize)

# Solving
if solve:
    # Create a solver
    opt = pyo.SolverFactory('gurobi')
    opt.options['NonConvex'] = 2

    # Create a model instance and optimize
    results = opt.solve(model)
    # model.pprint()

    # Writing results to system components
    for component in system.components:
        
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
             round(component.installed/1e3,1), 'kW(h)')
            
            
    print()
    print('Total system cost (objective)= ', round(value(model.capitalcost)/1e3,1), 'k€')
    system.cost = value(model.capitalcost)

    
    system.to_pickle()
    
    # df.drop('Energy', axis = 1, inplace= True)
    # df['Balance'] = df.sum(axis= 1)
    # if df.Balance.sum() > 1e-5:
    #     print()
    #     print('----------->> WARNING: balance is non-zero')

