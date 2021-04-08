import pandas as pd
import numpy as np
import pyomo.environ as pyo
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot

# import the Local Energy System Optimizer
import LESO

time = list(range(0,48))

max_MW = 10e6 

# Initiate components to consider
pv = LESO.PhotoVoltaic('full-south-pv', dof = True, upper = max_MW )
wind = LESO.Wind('wind-turbine', dof = True, upper = max_MW)
battery = LESO.Lithium('ESS', dof = True, upper = 2e6, startingSOC = 0.2)
charger = LESO.FastCharger('load')
grid = LESO.Grid('200KVA')

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


def fb(model, i):
    return (dofs[i].lower, dofs[i].upper)

model.sizing = pyo.Var( dofs, domain = pyo.Reals, initialize = 0, bounds = fb)



# Create control variables
model.control_state = pyo.Var(controlables, domain = pyo.Reals, initialize = 0)

def power(model, component, t):
    
    key = component.__str__()
    
    # power is controlable (battery, grid)
    if hasattr(component, 'power_control'):
        
        # controlable component is a dof
        if component.dof:
            ppower = model.sizing[key]*\
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
            ppower = model.sizing[key]*\
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
        key = component.__str__()
        
        if isinstance(component, LESO.Lithium):
            
            
            model.constr.add(
                (0, model.control_state[component.__str__()+'.energy',t], 1)
                )
        
        if isinstance(component, LESO.Grid):
            
            model.constr.add(
                (-1, model.control_state[key+'.power',t], 1)
                )
            
    
    if not t == time[-1]:
        
        for component in system.components:
            if isinstance(component, LESO.Lithium):
                key = component.__str__()
                
                # battery charging dynamics
                model.constr.add(
                    model.control_state[key+'.energy',t+1] == model.control_state[key+'.energy',t] - model.control_state[key+'.power',t]
                    )
                
                # respect the EP ratio
                model.constr.add(
                    (-1/component.EP_ratio, model.control_state[key+'.power', t], 1/component.EP_ratio)
                    )

    
             

model.capitalcost = pyo.Objective(
                    expr = sum(model.sizing[key] * component.cost for key, component in dofs.items()), 
                    sense = pyo.minimize)








if True:
    # Create a solver
    opt = pyo.SolverFactory('gurobi')
    opt.options['NonConvex'] = 2
    
    # Create a model instance and optimize
    results = opt.solve(model)
    model.pprint()
    
    
    for t in time:
        for key, component in dofs.items():
            
            if hasattr(component, 'power_control'):
                component.state.power.iloc[t-1] = model.control_state[key+'.power',t]()*model.sizing[key]()
    
       
    for key in dofs:
        print(f"{key} = ", round(model.sizing[key]()/1e3,2), 'kW')
        dofs[key].installed = model.sizing[key]()


df = pd.DataFrame({'Time' : time,
                        'pv_power' : model.sizing['pv1'].value * pv.state.power[time],
                        'wind_power' : 1 * wind.state.power[time], # model.sizing['wind1'].value
                        'load' : charger.state.power[time]})

df['battery_energy'] = [model.sizing['lithium1'].value * model.control_state[('lithium1.energy',t)].value for t in time]
df['battery_power'] = [model.sizing['lithium1'].value * model.control_state[('lithium1.power',t)].value for t in time]
df['grid'] = [grid.installed * model.control_state[('grid1.power',t)].value for t in time]




fig1 = px.line(df, x=df.Time, y=df.columns)
plot(fig1)