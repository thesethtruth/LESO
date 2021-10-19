# required packages
import pandas as pd
import numpy as np
import warnings
import pickle
import json
from datetime import datetime
import os
from typing import Optional

# for optimizing
import pyomo.environ as pyo

# module with default values
import LESO.defaultvalues as defs
from LESO.dataservice import get_pvgis
import LESO.optimizer.core as core
from LESO.optimizer.core import power
from LESO.optimizer.core import set_objective
from LESO.optimizer.postprocess import process_results
from LESO.components import FinalBalance
from LESO.test import attribute_test
from LESO.finance import set_finance_variables

class System:
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
    _default_parameters = defs.system_parameters

    def __init__(self, lat, lon, model_name="LESO energy model", **kwargs):

        self.lat = lat
        self.lon = lon
        self.name = model_name
        self.components = list()

        # Set default values as instance attribute
        self.default_parameters()
        # Let custom component setter handle the custom values
        self.custom_parameters(**kwargs)

        # initiate financial parameters based on values provided
        set_finance_variables(self)

    def __str__(self):
        return self.name

    def add_components(self, component_itterable):

        for component in component_itterable:
            attribute_test(component)
            set_finance_variables(component, self)
            self.components.append(component)

        # sort based on merit
        merit_list = []
        for component in self.components:
            merit_list.append(defs.merit_order[component.merit_tag])

        components = np.array(self.components)
        merit_list = np.array(merit_list)
        inds = merit_list.argsort()

        sorted_comps = components[inds]

        self.components = list(sorted_comps)
    
    def default_parameters(self):
        for key, value in self._default_parameters.items():
            setattr(self, key, value)
        pass

    def custom_parameters(self, **kwargs):
        for key, value in kwargs.items():
            if key in self._default_parameters.keys():
                setattr(self, key, value)
            else:
                print(f"Warning: Invalid input argument supplied -- default used: {key} for {self}")
        pass

    def update_component_attr(self, attribute, value, overwrite_zero=False):
        for component in self.components:
            if hasattr(component, attribute):
                if getattr(component, attribute) != 0 or overwrite_zero:
                    setattr(component, attribute, value)

    def fetch_input_data(self, lat=None, long=None):

        if lat is not None:
            self.lat = lat
        if long is not None:
            self.lon = long

        self.tmy = get_pvgis(self.lat, self.lon)

    def calculate_time_series(self):

        print()
        print(
            "Calculating time series for {} components...".format(len(self.components))
        )

        for component in self.components:

            try:
                component.calculate_time_serie(self.tmy)
            except AttributeError:
                print(
                    f"---> Note: {component} does not have 'calculate_"
                    + "time_serie' function"
                )

    def calculate_merit_balance(self):

        for component in self.components:
            if component.dof:
                component.dof = False
                component.installed = component.default_values["installed"]
                warnings.warn(
                    f"component '{component.name}' set to DOF, \
                        reverting to default installed capacity value: {component.installed/1e3} kW(h)"
                )

        from LESO.scenario.balancing import merit_order

        self.balance = merit_order(
            self.components, self.merit_order_dict, self.start_date
        )

    # model chain for all procedures for running merit-order
    def merit_order(self, store=True, filepath=None):

        self.last_call = "merit_order"

        if not any(
            [isinstance(component, FinalBalance) for component in self.components]
        ):
            warnings.warn(
                "No instance of component class LESO.components.FinalBalance found. Added "
                + "automatically with allowance for underload."
            )
            self.add_components([FinalBalance(positive=True)])

        print()
        print("Merit order calculation started...")
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
            year = 8760  # h
            t_span = year
            t_min = 0
            time = list(range(t_min, t_min + t_span))

        # Define model and add time
        self.model = pyo.ConcreteModel()
        self.model.constraint_ID = "constraints"
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

            if hasattr(component, "construct_constraints"):

                # for each component with constraints
                component.construct_constraints(self)

    def pyomo_power_balance(self):

        constraints = getattr(self.model, self.model.constraint_ID)

        for t in self.time:
            constraints.add(
                0
                == sum(power(self.model, component, t) for component in self.components)
            )

    def pyomo_add_objective(self, objective=None):

        return set_objective(self, objective)
    
    def pyomo_add_additional_constraints(self, additional_constraints: Optional[list]=None):

        if additional_constraints is not None:

            # fail safe if a single additional_constraint is given, instead of expected list/iterable
            try:
                for additional_constraint in additional_constraints:
                    additional_constraint(self)
            except TypeError:
                additional_constraints(self)

    def pyomo_solve(self, solver="gurobi", noncovex=False, tee=False):

        opt = pyo.SolverFactory(solver)
        if noncovex:
            opt.options["NonConvex"] = 2

        opt.options["IterationLimit"] = 200000
        # opt.options['BarHomogeneous'] = 1
        opt.options["Method"] = 1

        self.model.results = opt.solve(self.model, tee=tee)

    def pyomo_post_process(self, unit="k"):

        process_results(self, unit=unit)

    def optimize(
        self,
        objective="osc",
        additional_constraints: Optional[list] = None,
        time=None,
        store=False,
        filepath=None,
        solve=True,
        solver="gurobi",
        nonconvex=False,
        unit="k",
        tee=False,
    ):
        """ 
        Toolchain called to use all methods needed to apply optimization to the defined
        problem. 
            Passes all input arguments to the desired functions. 
        """
        self.last_call = "optimize"
        # load TMY
        self.fetch_input_data()

        # Issue the command for every component to calculate its feed-in on TMY data
        self.calculate_time_series()

        self.pyomo_init_model(time=time)

        self.pyomo_constuct_constraints()

        self.pyomo_power_balance()

        self.pyomo_add_objective(objective=objective)

        self.pyomo_add_additional_constraints(additional_constraints=additional_constraints)

        if solve:
            self.pyomo_solve(solver=solver, noncovex=nonconvex, tee=tee)

            # check solver status before proceeding to post process options
            if pyo.check_optimal_termination(self.model.results):
                if solve:
                    self.pyomo_post_process(unit=unit)

                self.pyomo_extract_results()

                if store:
                    self.to_json(filepath=filepath)
            else:
                warnings.warn("LESO: Exiting without processing a solution since non-optimal solver exit.")
        
    def pyomo_print(self, time=None):
        """
        Method to inspect constraints and objective function.
            Sets time to single value array to yield single expression constraints.
            Calls system.optimize with solve set to False to construct model.
        """

        # set time to 1 for readable prints of constraints
        if time is None:
            time = [0]

        self.optimize(solve=False, time=time)

        self.model.pprint()
    
    def pyomo_extract_results(self):
        """
        Extract the results and store to dict as attr of system. 
            Parses pyomo results to a comprehensive dict. 
        """

        print("Splitting the power of sources/sinks to pos/neg")
        for component in self.components:
            if not hasattr(component, "power_control"):
                component.split_states()
                

        # small helper function
        def _date_to_string(component):
            return np.datetime_as_string(component.state.index.values).tolist()

        from LESO import AttrDict
        
        results = AttrDict()
        components_dict = AttrDict()

        for component in self.components:
            _key = component.__str__()
            state = component.state

            compdict = AttrDict({
                "state": AttrDict({
                    column: state[column].values.tolist()
                    for column in state.columns
                    if column != "power"
                }),
                "styling": component.styling,
                "settings": AttrDict({
                    key: getattr(component, key)
                    for key in component.default_values
                    if key != "styling"
                }),
                "name": component.name,
            })
            
            styling = component.styling
            compdict.update({"styling":styling})
            # add component dict to components
            components_dict.update({_key:compdict})

        results.update({"components":components_dict})

        sysdict = AttrDict({
            "system": {
                "dates": _date_to_string(self.components[0]),
                "name": self.name,
                "date": datetime.now().isoformat(),
                "last_call": self.last_call,
                "installed_capacities": getattr(
                    self, "optimization_result", "Not available"
                ),
                "objective_outcome": self.model.objective.expr(),
            }
        })

        results.update(sysdict)

        
        self.results = results

        return None

    def info(self, print_it=False):
        info = []
        info.append("----{}----".format(self.name))
        info.append("Components in model:")
        for component in self.components:
            info.append(component.__str__() + ": " + component.name)

        if print_it:
            for line in info:
                print(line)
        else:
            return info

    def to_pickle(self, filepath=None):

        if filepath is None:
            filepath = os.path.join(os.getcwd(), self.name + ".pkl")

        picklefile = open(filepath, "wb")
        pickle.dump(self, picklefile)
        picklefile.close()

        print()
        print("Saved and pickled model instance to {}".format(filepath))

    @staticmethod
    def read_pickle(filepath):

        import pickle

        salty_model_instance = open(filepath, "rb")
        loaded_model_instance = pickle.load(salty_model_instance)
        salty_model_instance.close()

        print()
        print("Opened and unpickled {}".format(loaded_model_instance.name))

        return loaded_model_instance

    def to_json(self, filepath=None):
        
        save_info = self.results

        if filepath is None:
            name = save_info["system"]["name"].replace("\/:*?<>|", "")
            date = save_info["system"]["date"][:17].replace(":", "")
            last_call = self.last_call
            filepath = f"cache/{name}__{date}__{last_call}.json"

        with open(filepath, "w") as outfile:
            json.dump(save_info, outfile)

        return None