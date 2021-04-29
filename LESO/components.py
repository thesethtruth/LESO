# -*- coding: utf-8 -*-
# --> LESO == Local Energy System Optimalization


# required packages
import pandas as pd
import numpy as np

# for optimizing
import pyomo.environ as pyo
from pyomo.environ import value

# module with default values
import LESO.defaultvalues as defs
import LESO.feedinfunctions as feedinfunctions
import LESO.functions as functions
import LESO.optimizer.util as util

class Component():
    """
    The mother of all components
        These classes as children:
    1. SourceSinks      ~ generators/loads/hybrid (e.g. grid)
    2. Storages         ~ components with both power and energy
    3. Transformers     ~ energy form transformers (p2h, p2H2) [unused]
    4. Collectors       ~ sums input and equals output [unused]
    """
    
    dof = False
        
    def __init__(self):
        self.unit = 1
    
    def default(self):
        
        # start_date to be used
        self.start_date = defs.start_date
        self.keylist = []
        # empty states dataframe
        self.state = pd.DataFrame(0,
            index = pd.date_range(
                self.start_date, 
                periods=8760, 
                freq="1h"), 
            columns = self.states)
        
        for key, value in self.default_values.items():
            setattr(self, key, value)
            
    def custom(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.default_values.keys():
                setattr(self, key, value) 
            elif key == 'dof' and value == 1:
                    self.dof = value
                    self.installed = 1
            else:
                print('Warning: Invalid input argument supplied -- default used')
    @property
    def control_states(self):
        return {key: 0 for key in self.states}
            
#%%                

class SourceSink(Component):
    pass
        
class Storage(Component):
    
    @staticmethod
    def power_control():
        raise NotImplementedError 
    pass

class Collector(Component):
    pass
    
class Transformer(Component):
    pass

#%%
class PhotoVoltaic(SourceSink):
    
    instances = 0
    
    # read default values 
    default_values = defs.pv
    states = ['power']
               
    def __init__(self, name, **kwargs):
        
        # Set default values as instance attribute
        self.default()
        
        # Let custom component setter handle the custom values
        self.custom(**kwargs)
        
        PhotoVoltaic.instances +=1
        self.number = PhotoVoltaic.instances
        self.name = name
            
    @property
    def area(self):
        return self.installed/self.module_power*self.module_area
    
    @area.setter
    def area(self, value):
        return print('---> Note: Change the module power or -area to change this variable')
        
    def __str__(self):
        return "pv{number}".format(number = self.number)
    
    def calculate_time_serie(self, tmy):

        self.state.power = feedinfunctions.PVpower(self, tmy)

class Dump(SourceSink):
    
    # read default values 
    default_values = defs.dump
    states = ['power']
    control_states = {'power':1}
               
    def __init__(self, **kwargs):
        
        # Set default values as instance attribute
        self.default()
        
        # Let custom component setter handle the custom values
        self.custom(**kwargs)

        self.name = self.__str__()
        
    def __str__(self):
        return "FinalBalance"
    
    def power_control(self, balance_in):
        raise NotImplementedError(  "Make sure the final balance" +
                                    "gets stored in this component")
    def construct_constraints(self, system):
        
        util.final_balance_power_control_constraints(system.model, self)


    
class Wind(SourceSink):
        
    instances = 0
    default_values = defs.wind
    states = ['power']
    
    def __init__(self, name, **kwargs):
        
        # Set default values as instance attribute
        self.default()
        
        # Let custom component setter handle the custom values
        self.custom(**kwargs)
        
        Wind.instances +=1
        self.number = Wind.instances
        self.name = name
    
    def __str__(self):
        return "wind{number}".format(number = self.number)
    
    def calculate_time_serie(self, tmy):
        
        self.state.power = feedinfunctions.windpower(self, tmy)
    
class Lithium(Storage):
    
    instances = 0
    default_values = defs.lithium
    states = ['power', 'energy']
    control_states = {'power': 1, 'energy': 1}
        
    def __init__(self, name, **kwargs):
        
        # Set default values as instance attribute
        self.default()
        
        # Let custom component setter handle the custom values
        self.custom(**kwargs)
        
        Lithium.instances +=1
        self.number = Lithium.instances
        self.name = name
    
    @property
    def dischargepower(self):
        return self.installed / self.EP_ratio
    
    @dischargepower.setter
    def dischargepower(self, value):
        return print('---> Note: Change the EP ratio to change this variable')
    
    def __str__(self):
        return "lithium{number}".format(number = self.number)
    
    def power_control(self, balance_in):
        
        from LESO.scenario.balancing import battery_power_control
        
        [self.state.power, 
         self.state.energy] = battery_power_control(self, balance_in)

    def construct_constraints(self, system):

        util.battery_control_constraints(system.model, self) 

    
    
class FastCharger(SourceSink):
    
    instances = 0
    default_values = defs.fastcharger
    states = ['power']
        
    def __init__(self, name, **kwargs):
        
        # Set default values as instance attribute
        self.default()
        
        # Let custom component setter handle the custom values
        self.custom(**kwargs)
        
        FastCharger.instances +=1
        self.number = Lithium.instances
        self.name = name
    
    def __str__(self):
        return "fastcharger{number}".format(number = self.number)
    
    def calculate_time_serie(self, *args):
        
        self.state.power = functions.calculate_charging_demand(self)
    
class Consumer(SourceSink):
    
    instances = 0
    default_values = defs.consumer
    states = ['power']
    
    def __init__(self, name, **kwargs):
        
        # Set default values as instance attribute
        self.default()
        
        # Let custom component setter handle the custom values
        self.custom(**kwargs)
        
        Consumer.instances +=1
        self.number = Lithium.instances
        self.name = name
    
    def __str__(self):
        return "consumer{number}".format(number = self.number)
    
    def calculate_time_serie(self, *args):
        
        self.state.power = functions.read_consumption_profile(self)

class Grid(SourceSink):
    
    instances = 0
    default_values = defs.grid
    states = ['power']
    control_states = {'power':1}
    
    def __init__(self, name, **kwargs):
        
        # Set default values as instance attribute
        self.default()
        
        # Let custom component setter handle the custom values
        self.custom(**kwargs)

        Grid.instances +=1
        self.number = Grid.instances
        self.name = name
    
    def __str__(self):
        return "grid{number}".format(number = self.number)
    
    def power_control(self, balance_in):
        
        from LESO.scenario.balancing import grid_power_control
        
        self.state.power = grid_power_control(self, balance_in)

    def construct_constraints(self, system):

        util.direct_power_control_constraints(system.model, self)

ComponentClasses = {
    "PV system" : PhotoVoltaic, 
    "Wind turbine": Wind, 
    "Lithium-ion ESS": Lithium, 
    "DC fastcharger": FastCharger,
    "Electric consumer": Consumer, 
    "Grid connection": Grid,
     "Curtailment/underload": Dump,
}