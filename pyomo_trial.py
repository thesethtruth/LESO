import pandas as pd
import numpy as np
import pyomo.environ as pyo
import matplotlib.pyplot as plt

# import the Local Energy System Optimizer
import LESO

time = list(range(0,24))

max_MW = 10e6 

# Initiate components to consider
pv = LESO.PhotoVoltaic('full-south-pv', dof = True, upper = max_MW )
wind = LESO.Wind('wind-turbine', dof = True, upper = max_MW)
battery = LESO.Lithium('ESS', dof = True, upper = max_MW)
charger = LESO.FastCharger('load')
# grid = LESO.Grid('200KVA')

# set system to Utrecht location
system = LESO.System(52, 5)

# load TMY
system.fetch_input_data()

# add components to the system (Model Class)
system.add_components([pv, wind, battery, charger])

# Issue the command for every component to calculate its feed-in on TMY data
system.calculate_time_series()





# Declare the degrees of freedom in the sys
dofs = {}
for component in system.components:
    if component.dof is True:
        dofs.update({component.__str__(): component})

controlables = []
for component in system.components:
    if hasattr(component, 'power_control'):
        for state in component.control_states:
            for t in time:
                
                controlables.append([component.__str__()+'.'+state, t])
                



# Create model
model = pyo.ConcreteModel()

# Create DOF variables
# for key in dofs:
#     setattr(
#         model,
#         key+'_size',
#         pyo.Var(
#             bounds = (
#                     dofs[key].lower,
#                     dofs[key].upper,
#                     )
#             )        
#         )

model.dofs = pyo.Var( dofs, domain = pyo.Reals, initialize = 1)



# Create control variables
model.control_state = pyo.Var(controlables, bounds=(-1, 1))

def power(model, component, t):
    
    key = component.__str__()
    
    # power is controlable (battery, grid)
    if hasattr(component, 'power_control'):
        
        # controlable component is a dof
        if component.dof:
            ppower = getattr(model, key + '_size')*\
                      model.control_state[key +'.power', t]
        
        # controlable component is not a dof, use installed capacity
        else:
              ppower = component.installed*\
                      model.control_state[key +'.power', t]
            
    # must-meet loads (charger, consumer)
    elif component.merit_tag == 'MM':
        ppower = component.state.power[t] 
    
    # is VRE (wind, pv)
    elif component.merit_tag == 'VRE':
        
        # VRE component is a dof
        if component.dof:
            ppower = getattr(model, key + '_size')*\
                      component.state.power[t] 
        
        # VRE component is not a dof, use installed capacity
        else:
              ppower = component.installed*\
                      component.state.power[t] 
        
    return ppower

# ==========================CONSTRAINTS=======================================

# Initialize constraint lists
model.balance = pyo.ConstraintList()
model.constr = pyo.ConstraintList()


# static constraint (initialized or constant)
for component in system.components:
    
    
    if isinstance(component, LESO.Lithium):
        
        # battery is loaded in first time step
        model.constr.add(
            model.control_state[component.__str__()+'.energy', time[0]] == component.startingSOC
            )

# dynamic constraints (function of time)
for t in time: 
    
    # power balance
    model.balance.add( 0 <= sum(power(model,component,t) for component in system.components ) )
    
    # prevent non-negative energy from occuring (allowing power)
    for component in system.components:
        if isinstance(component, LESO.Lithium):
            
            model.constr.add(
                (0, model.control_state[component.__str__()+'.energy',t], 1)
                )
            
            
    
    if not t == time[-1]:
        
        for component in system.components:
            if isinstance(component, LESO.Lithium):
                
                # battery charging dynamics
                model.constr.add(
                    model.control_state[component.__str__()+'.energy',t+1] == model.control_state[component.__str__()+'.energy',t] - model.control_state[component.__str__()+'.power',t]
                    )
                
                # respect the EP ratio
                model.constr.add(
                    (-1/component.EP_ratio, model.control_state[component.__str__()+'.power', t], 1/component.EP_ratio)
                    )
    
             

model.capitalcost = pyo.Objective(
                    expr = sum(getattr(model, key+ '_size') * component.cost for key, component in dofs.items()), 
                    sense = pyo.minimize)








if False:
    # Create a solver
    opt = pyo.SolverFactory('gurobi')
    opt.options['NonConvex'] = 2
    
    # Create a model instance and optimize
    results = opt.solve(model)
    model.pprint()
    
    
    # for t in time:
    #     for key, component in dofs.items():
            
    #         if hasattr(component, 'power_control'):
    #             component.state.power.iloc[t-1] = model.control_state[key+'.power',t]()*model.dofs[key]()
    
       
    # for key in dofs:
    #     print(f"{key} = ", round(model.dofs[key]()/1e6,2), ' MW')
    #     dofs[key].installed = model.dofs[key]()


model.pprint()