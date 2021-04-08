import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import value
import numpy as np

import LESO


# Constants
t_span = 168*52
t_min = 0
upper_limit = 10e6 # == 10 MW

time = list( range ( t_min, t_min + t_span) )

# Initiate components to consider
pv = LESO.PhotoVoltaic('full-south-pv', dof = True)
wind = LESO.Wind('wind-turbine', dof = True)
battery = LESO.Lithium('ESS', dof = True, startingSOC = 0.2)
charger = LESO.FastCharger('load')
grid = LESO.Grid('200tVA')

# set system to Utrecht location
system = LESO.System(52, 5)

# load TMY
system.fetch_input_data()

# add components to the system (Model Class)
system.add_components([pv, wind, battery, charger, grid])

# Issue the command for every component to calculate its feed-in on TMY data
system.calculate_time_series()

# Create model
model = pyo.ConcreteModel()

# constant variables
model.bat_Esize = pyo.Var(bounds=(0,upper_limit))
model.PVsize = pyo.Var(bounds=(0,upper_limit))
model.Windsize = pyo.Var(bounds=(0,upper_limit))
model.curtail_P = pyo.Var(time, bounds=(-1* upper_limit, 0))

# time dependent variables
model.bat_Ppos = pyo.Var(time, domain = pyo.NonNegativeReals, initialize = 0)
model.bat_Pneg = pyo.Var(time, domain = pyo.NonPositiveReals, initialize = 0)
model.bat_P = pyo.Var(time)
model.bat_E = pyo.Var(time)

# Define objective function
def ObjRule(model):
    return  model.PVsize*pv.cost  \
            + model.Windsize*wind.cost  \
            + model.bat_Esize*battery.cost  \
            + sum((model.bat_Ppos[t]-model.bat_Pneg[t])*battery.cost/1000 for t in time)


model.OBJ = pyo.Objective(rule = ObjRule, sense = pyo.minimize)

model.c1 = pyo.ConstraintList()

# Initial battery soc
model.c1.add(model.bat_E[0] == battery.startingSOC)


# Charging battery
for t in time:
    if t == time[-1]:
        pass
    else:
        model.c1.add(model.bat_E[t+1] == model.bat_E[t] - model.bat_P[t])


# Time variable constraints
for t in time:
    
    # energy balance
    model.c1.add(0 == model.bat_P[t] + model.Windsize*wind.state.power[t] + model.PVsize*pv.state.power[t] + charger.state.power[t] + model.curtail_P[t])
    
    # battery energy should be positive
    model.c1.add(0 <= model.bat_E[t])
    
    # limit the battery energy state to maximum of size
    model.c1.add(model.bat_E[t] <= model.bat_Esize)
    
    # limit battery DISCHARGING to bat size
    model.c1.add(model.bat_P[t] <= 1/battery.EP_ratio * model.bat_Esize)
    
    # limit battery CHARGING to bat size
    model.c1.add(model.bat_P[t] >= -1/battery.EP_ratio * model.bat_Esize)
    
    # Make total power the sume of positive and negative instances of powercurve
    model.c1.add(model.bat_P[t] == model.bat_Ppos[t] + model.bat_Pneg[t])



# Create a solver
opt = pyo.SolverFactory('gurobi')
opt.options['NonConvex'] = 2

# Create a model instance and optimize
results = opt.solve(model)
# model.pprint()

df = pd.DataFrame({ 'PV power' : model.PVsize.value * pv.state.power[time],
                    'Wind power' : model.Windsize.value * wind.state.power[time],
                    'Charging load' : charger.state.power[time]})

df['bPower'] = [model.bat_P[t].value for t in time]
df['Battery charging'] = df['bPower'].where(df['bPower']<0, 0)
df['Battery discharging'] = df['bPower'].where(df['bPower']>0, 0)
df['Ppos'] = [model.bat_Ppos[t].value for t in time]
df['Pneg'] = [model.bat_Pneg[t].value for t in time]

df.drop(['bPower'], axis=1, inplace=True)
df['Curtailment'] = [model.curtail_P[t].value for t in time]


df['Battery energy'] = [model.bat_E[t].value for t in time]

print()
print('Battery size                 = ', round(model.bat_Esize.value/1e3,1), 'kWh')
print('Wind installed               = ', round(model.Windsize.value/1e3,1), 'kW')
print('PV installed                 = ', round(model.PVsize.value/1e3,1), 'kW')
print("-------------")
print('Total system cost (objective)= ', round(value(model.OBJ)/1e3,1), 'k€')


df.to_pickle('latest_result.pkl')



