# required packages
import pandas as pd
import numpy as np
import warnings
import pickle
import json
from datetime import datetime
from pyomo.core.base.block import components

# for optimizing
import pyomo.environ as pyo
from pyomo.environ import value

# module with default values
import LESO.defaultvalues as defs
from LESO.dataservice import get_pvgis
import LESO.optimizer.util as util
from LESO.optimizer.util import power
from LESO.optimizer.util import set_objective
from LESO.optimizer.postprocess import process_results
from LESO.components import FinalBalance
from LESO.test import attribute_test
from LESO.finance import set_finance_variables

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
    
    def __init__(self, latitude, longitude, model_name='LESO model'):
        
        self.latitude = latitude
        self.longitude = longitude
        self.name = model_name
        self.merit_order_dict = defs.merit_order
        self.start_date = defs.start_date
        self.components = list()
        
        # financials
        self.lifetime = defs.system_lifetime
        self.interest = defs.interest
        self.exp_inflation_rate = defs.exp_inflation_rate
        set_finance_variables(self)

    def __str__(self):
        return self.name
    
    def add_components(self, component_itterable):
        
        for component in component_itterable:
            attribute_test(component)
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

    def update_component_attr(self, attribute, value, overwrite_zero=False):
        for component in self.components:
            if hasattr(component, attribute):
                if getattr(component, attribute) != 0 or overwrite_zero:
                        setattr(component, attribute, value)

    def fetch_input_data(self, lat = None, long = None):
        
        if lat is not None:
            self.latitude = lat
        if long is not None:
            self.longitude = long
        
        self.tmy = get_pvgis(self.latitude, self.longitude)
    
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
    def merit_order(self, store=True, filepath=None):

        self.last_call = 'merit_order'
        
        
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

        if store:
            self.to_json(filepath=filepath)

    
    def pyomo_init_model(self, time=None):
        """
        Initializes the Pyomo model, adds modes for power/energy control and adds the
        DOF variables as needed. 
        """
        
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

        # Initialize constraint list
        if not hasattr(self.model, self.model.constraint_ID):
                setattr(self.model, self.model.constraint_ID, pyo.ConstraintList())

        for component in self.components:
            component.initializePyomoVariables(self.model)
    
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

        return set_objective(self, objective)
    
    def pyomo_solve(self, solver = 'gurobi', noncovex = False):

        opt = pyo.SolverFactory(solver)
        if noncovex:
            opt.options['NonConvex'] = 2
            
        opt.options['BarHomogeneous'] = 1
        self.model.results = opt.solve(
            self.model,
            tee=True)

    def pyomo_post_process(self, unit='k'):
        
        process_results(self, unit=unit)

    def optimize(
            self, 
            objective='tco',
            time=None,
            store=False,
            filepath=None,
            solve=True,
            solver='gurobi',
            nonconvex=False,
            unit='k'
            ):
        """

        """
        self.last_call = 'optimize'
        # load TMY
        self.fetch_input_data()

        # Issue the command for every component to calculate its feed-in on TMY data
        self.calculate_time_series()

        self.pyomo_init_model(time = time)

        self.pyomo_constuct_constraints()

        self.pyomo_power_balance()

        self.pyomo_add_objective(objective=objective)
        
        if solve:
            self.pyomo_solve(
                solver=solver,
                noncovex=nonconvex)

            self.pyomo_post_process(unit=unit)

        if store:
            self.to_json(filepath=filepath)
    
    def pyomo_print(self, time=None):
        
        # set time to 1 for readable prints of constraints
        if time is None:
            time = [0]

        self.optimize(solve=False, time = time)

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
    
    def to_json(self, filepath=None):

        
        print('proceeding to hacky method of splitting power to pos/neg')
        for component in self.components:
            component.split_states()
        
        # small helper function
        def _date_to_string(component):
            return np.datetime_as_string(component.state.index.values).tolist()

        save_info = dict()
        for component in self.components:
            _key = component.__str__()
            state = component.state

            compdict = {
                _key: 
                {
                'state': {column: state[column].values.tolist() for column in state.columns if column != 'power'},
                'styling': component.styling,
                'settings': { key: getattr(component, key) for key in component.default_values if key != 'styling'},
                'name': component.name,
                }
            }
            styling = dict(styling = component.styling)
            compdict[_key].update(styling)

            save_info.update(compdict)

        sysdict = {
            'system': 
            {
            'dates': _date_to_string(self.components[0]),
            'name': self.name,
            'date': datetime.now().isoformat(),
            'last_call': self.last_call,
            'optimization result': getattr(self, 'optimization_result', 'Not available')
            }
        }

        save_info.update(sysdict)

        if filepath is None:
            name = save_info['system']['name'].replace("\/:*?<>|",'')
            date =  save_info['system']['date'][:17].replace(':','')
            last_call = self.last_call
            filepath = f"cache/{name}__{date}__{last_call}.json"
        
        with open(filepath, "w") as outfile: 
            json.dump(save_info, outfile)

        