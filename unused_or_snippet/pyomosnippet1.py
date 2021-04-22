from pyomo.environ import *

model = ConcreteModel()

model.LumberJack = Var(within=NonNegativeReals, bounds=(0,6), initialize=1.5)
model.A = Set(initialize=['Scones', 'Tea'])
lb = {'Scones':2, 'Tea':4}
ub = {'Scones':5, 'Tea':7}
def fb(model, i):
   return (lb[i], ub[i])
model.PriceToCharge = Var(model.A, domain=PositiveIntegers, bounds=fb, initialize = 1)