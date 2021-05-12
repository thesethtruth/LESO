# required packages
import pandas as pd
import numpy as np
import warnings
import pickle

# for optimizing
import pyomo.environ as pyo
from pyomo.environ import value

# module with default values
import LESO.defaultvalues as defs
from LESO.pvgis import get
import LESO.optimizer.util as util
from LESO.optimizer.util import power
from LESO.optimizer.util import capital_cost
from LESO.components import FinalBalance

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

        for component in self.components:
            if component.dof:
                component.dof = False
                component.installed = component.default_values['installed']
                warnings.warn(
                        f"component '{component.name}' set to DOF, \
                        reverting to default installed capacity value: {component.installed/1e3} kW(h)")
        
        from LESO.scenario.balancing import merit_order
        
        self.balance = merit_order(
                            self.components,
                            self.merit_order_dict,
                            self.start_date
                        )
    
    
    # model chain for all procedures for running merit-order
    def run_merit_order(self):
        
        
        if not any([isinstance(component, FinalBalance) for component in self.components]):
            warnings.warn(
                "No instance of component class LESO.components.FinalBalance found. Added "+\
                "automatically with allowance for underload."
            )
            self.add_components([FinalBalance(positive=True)])
        
        print()
        print('Merit order calculation started...')
        self.fetch_input_data()
        self.calculate_time_series()
        self.calculate_merit_balance()

        print('proceeding to hacky method of splitting power to pos/neg')
        for component in self.components:
            component.split_states()
    
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
        
        util.init_model(self, self.model, self.time)
    
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
        
        for t in self.time:
            constraints.add( 0 == sum(power(self.model,component,t) for component in self.components ))

    
    def pyomo_add_objective(self, objective = None):

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

        if print_it:
            for line in info:
                print(line)
        else:
            return info
            
    def to_pickle(self, folder = 'cache'):
        
        location_string = folder+'/'+self.name+'.pkl'
        picklefile = open(location_string, 'wb')
        pickle.dump(self, picklefile)
        picklefile.close()
       
        print() 
        print('Saved and pickled model instance to {}'.format(location_string))
        
    @staticmethod
    def read_pickle(filepath):
        
        import pickle
        salty_model_instance = open(filepath, 'rb')
        loaded_model_instance = pickle.load(salty_model_instance)
        salty_model_instance.close()
        
        print() 
        print('Opened and unpickled {}'.format(loaded_model_instance.name)) 
        
        return loaded_model_instance