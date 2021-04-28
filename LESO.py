# -*- coding: utf-8 -*-
# --> LESO == Local Energy System Optimalization


# required packages
import pandas as pd
import numpy as np

# for optimizing
import pyomo.environ as pyo
from pyomo.environ import value

# module with default values
import defaultvalues as defs



class System():
    """
        Object Oriented Programming Mothership
        OOPM
    contains components via .components as a list
    
    Construct inputs:
        latitude
        longitude
        model_name
        
    Alternative construct:
        .from_pickle(model_name)
            --> Used to unpickle a model which was previously defined
    
    methods:
        .add_components(components_list)
            --> Add components to the system
        .fetch_input_data()
            --> Fetches input data through API where applicable
        .calculate_time_series(tmy)
            --> Pushed input data to components 
            --> Executes .calculate_time_serie() on component instance level
        .merit_order()
            --> 'Model chain' used for calculating model results based on 
                merit order calculations
        .to_pickle()
            --> Saves current model in folder (default: models) under instance
            name (__str__) in binary format
    """
    
    def __init__(self, latitude, longitude, model_name = 'LESO model'):
        
        self.latitude = latitude
        self.longitude = longitude
        self.name = model_name
        self.merit_order_dict = defs.merit_order
        self.start_date = defs.start_date
        
        self.components = list()
        
        
    def __str__(self):
        return self.name
    
    def add_components(self, component_itterable):
        
        for component in component_itterable:
            self.components.append(component)
        
        # sort based on merit
        merit_list = []
        for component in self.components:
            merit_list.append(
                defs.merit_order[component.merit_tag]
                )
        
        components = np.array(self.components)
        merit_list = np.array(merit_list)
        inds = merit_list.argsort()

        sorted_comps = components[inds]

        self.components = list(sorted_comps)


    def fetch_input_data(self, lat = None, long = None):
        
        if lat is not None:
            self.latitude = lat
        if long is not None:
            self.longitude = long
            
        
        from API import get
        
        self.tmy = get(self.latitude, self.longitude)
    
    def calculate_time_series(self):
        
        print()
        print(
            'Calculating time series for {} components...'.format(
            len(
                self.components
                )
            )
        )
        
        for component in self.components:
        
            try:
                component.calculate_time_serie(self.tmy)
            except AttributeError:
                print(
                    f"---> Note: {component} does not have 'calculate_" + 
                    "time_serie' function"
                )
                
    def calculate_merit_balance(self):
        
        from balancing import merit_order
        
        self.balance = merit_order(
                            self.components,
                            self.merit_order_dict,
                            self.start_date
                        )
    
    
    # model chain for all procedures for running merit-order
    def run_merit_order(self):
        
        print()
        print('Merit order calculation started...')
        self.fetch_input_data()
        self.calculate_time_series()
        self.calculate_merit_balance()
    
    def pyomo_init_model(self, time = None):
        """
        Initializes the Pyomo model, adds modes for power/energy control and adds the
        DOF variables as needed. 
        """
        
        self.constraint_ID = 'constraints'
        if time is None:
            # times
            year = 8760 #h
            t_span = year
            t_min = 0
            time = list( range ( t_min, t_min + t_span) )

        # Define model and add time
        self.model = pyo.ConcreteModel()
        self.model.constraint_ID = 'constraints'
        self.model.time = time
        self.time = time
        
        from pyoutil import init_model
        init_model(self, self.model, self.time)
    
    def pyomo_constuct_constraints(self):
        """
        Will call the 'construct_constraints' method of each component which has 
        this modehod. All is added to the constraint list given by 'self.model.constraint_ID'

            Adds all constraints per component.
        """

        for component in self.components:

            if hasattr(component, 'construct_constraints'):
                
                # for each component with constraints
                component.construct_constraints(self)
    
    def pyomo_power_balance(self):
        
        constraints = getattr(self.model, self.model.constraint_ID)
        
        from pyoutil import power

        for t in self.time:
            constraints.add( 0 == sum(power(self.model,component,t) for component in self.components ))

    
    def pyomo_add_objective(self, objective = None):

        from pyoutil import capital_cost
        self.model.capitalcost = pyo.Objective(
                            expr = sum(capital_cost(self.model, component) for component in self.components), 
                            sense = pyo.minimize)
    
    def pyomo_solve(self, store = True, solver = 'gurobi', noncovex = False):

        opt = pyo.SolverFactory(solver)
        if noncovex:
            opt.options['NonConvex'] = 2
        
        self.model.results = opt.solve(self.model)

        model = self.model
        time = self.time
        # Writing results to system components
        for component in self.components:
            
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
        self.cost = value(model.capitalcost)


        self.to_pickle()

    def pyomo_go(self, solve = True, **kwargs):
        
        # load TMY
        self.fetch_input_data()

        # Issue the command for every component to calculate its feed-in on TMY data
        self.calculate_time_series()

        time = kwargs.get('time', None)
        self.pyomo_init_model(time = time)

        self.pyomo_constuct_constraints()

        self.pyomo_power_balance()

        self.pyomo_add_objective()
        
        if solve:
            self.pyomo_solve()
    
    def pyomo_print(self):
        
        # set time to 1 for readable prints of constraints
        time = [0]

        self.pyomo_go(solve=False, time = time)

        self.model.pprint()

        


    def info(self, print_it = False):
        info = []
        info.append('----{}----'.format(self.name))
        info.append('Components in model:')
        for component in self.components:
            info.append(component.__str__() +": " + component.name)

        if print:
            print(info)
        else:
            return info
            
    def to_pickle(self, folder = 'models'):
        
        import pickle
        
        location_string = folder+'/'+self.name+'.pkl'
        picklefile = open(location_string, 'wb')
        pickle.dump(self, picklefile)
        picklefile.close()
       
        print() 
        print('Saved and pickled model instance to {}'.format(location_string))
        
    @staticmethod
    def from_pickle(model_name, folder = 'models'):
        
        import pickle
        
        location_string = folder+'/'+model_name+'.pkl'
        salty_model_instance = open(location_string, 'rb')
        loaded_model_instance = pickle.load(salty_model_instance)
        salty_model_instance.close()
        
        print() 
        print('Opened and unpickled {}'.format(loaded_model_instance.name)) 
        
        return loaded_model_instance
    



class Component():
    """
    The mothership of LESOx
        These classes as children:
    1. SourceSinks      ~ generators/loads/hybrid (e.g. grid)
    2. Storages         
    3. Transformers     ~ energy form transformers
    4. Collectors       ~ sums input and equals output (unused)
    """
    
    dof = False
        
    def __init__(self):
        self.unit = 1
    
    def default(self):
        
        # start_date to be used
        from defaultvalues import start_date
        self.start_date = start_date
        self.keylist = []
        # empty states dataframe
        self.state = pd.DataFrame(0,
            index = pd.date_range(
                start_date, 
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
        
        from feedinfunctions import PVpower
        
        self.state.power = PVpower(self, tmy)

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
        
        from pyoutil import final_balance_power_control_constraints
        final_balance_power_control_constraints(system.model, self)


    
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
        
        from feedinfunctions import windpower
        
        self.state.power = windpower(self, tmy)
    
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
        
        from balancing import battery_power_control
        
        [self.state.power, 
         self.state.energy] = battery_power_control(self, balance_in)

    def construct_constraints(self, system):

        from pyoutil import battery_control_constraints

        battery_control_constraints(system.model, self) 

    
    
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
        
        from functions import calculate_charging_demand
        
        self.state.power = calculate_charging_demand(self)
    
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
        
        from functions import read_consumption_profile
        
        self.state.power = read_consumption_profile(self)

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
        
        from balancing import grid_power_control
        
        self.state.power = grid_power_control(self, balance_in)

    def construct_constraints(self, system):

        from pyoutil import direct_power_control_constraints
        direct_power_control_constraints(system.model, self)

ComponentClasses = {
    "PV system" : PhotoVoltaic, 
    "Wind turbine": Wind, 
    "Lithium-ion ESS": Lithium, 
    "DC fastcharger": FastCharger,
    "Electric consumer": Consumer, 
    "Grid connection": Grid,
     "Curtailment/underload": Dump,
}