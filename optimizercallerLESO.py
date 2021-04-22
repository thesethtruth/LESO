import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import value
import numpy as np
import time

from LESO import System
import LESO
# Constants

max_MW = 10e6 

t = time.process_time()

# Initiate components to consider
pv = LESO.PhotoVoltaic('Full-south PV', dof = True, upper = max_MW )
pv2 = LESO.PhotoVoltaic('West PV', azimuth = 90, dof = True, upper = max_MW, cost = .55 )
pv3 = LESO.PhotoVoltaic('East PV', azimuth = -90, dof = True, upper = max_MW, cost =.55 )
wind = LESO.Wind('Wind turbine', dof = True, upper = max_MW)
battery = LESO.Lithium('ESS', dof = True, upper = 10e6, startingSOC = 0.2)
charger = LESO.FastCharger('DC fastcharger', installed = 3)
grid = LESO.Grid('200KVA', installed = 150e3)
dump = LESO.Dump(positive = False, upper = 50e3)

# set system to Utrecht location
system = System(52, 5)
# add components to the system (Model Class)
system.add_components([battery, dump, pv, pv2, pv3, wind, charger, grid])

# system.pyomo_print()
system.pyomo_go()

elapsed_time = time.process_time() - t

print(f"This took {elapsed_time} seconds")