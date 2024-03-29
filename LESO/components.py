# -*- coding: utf-8 -*-
# --> LESO == Local Energy System Optimalization


# required packages
from warnings import WarningMessage
import warnings
import pandas as pd
import numpy as np

# for optimizing
import pyomo.environ as pyo
from pyomo.environ import value

# module with default values
import LESO.defaultvalues as defs
import LESO.feedinfunctions as feedinfunctions
import LESO.functions as functions
import LESO.optimizer.core as core
from LESO.optimizer.preprocess import initializeGenericPyomoVariables
from LESO.dataservice import get_pvgis, get_dowa, etm_id_extractor_external


class Component:
    """
    The mother of all components
        These classes as children:
    1. SourceSinks      ~ generators/loads/hybrid (e.g. grid)
    2. Storages         ~ components with both power and energy
    3. Transformers     ~ energy form transformers (p2h, p2H2) [unused]
    4. Collectors       ~ sums input and equals output [unused]
    """
    # fallback option(s) for calculation rigidity
    pyoVar = 1

    def __init__(self):
        pass

    def default(self):

        # start_date to be used
        self.start_date = defs.start_date
        self.keylist = []
        # empty states dataframe
        self.state = pd.DataFrame(
            0,
            index=pd.date_range(self.start_date, periods=8760, freq="1h"),
            columns=self.states,
        )

        for key, value in self.default_values.items():
            setattr(self, key, value)

    def custom(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.default_values.keys():
                setattr(self, key, value)
                if key == "dof" and value == 1:
                    self.dof = value
                    self.installed = 1
            else:
                print(f"Warning: Invalid input argument supplied -- default used: {key} for {self}")
        pass

    @property
    def control_states(self):
        return {key: 0 for key in self.states}

    def split_states(self):
        power = self.state.power

        self.state["power [+]"] = power.where(power > 0, 0.0)
        self.state["power [-]"] = power.where(power < 0, 0.0)
    
    def get_variable_cost(self, pM):
        return NotImplemented
    
    @property
    def replacement(self):
        return 0.5 * self.capex
    
    def sum_by_month(self):

        self.state['month'] = self.state.index.month_name()
        self.monthly_state = self.state.groupby('month', sort=False).sum()

        return None
    
    def initializePyomoVariables(self, pM):
        """" Default fallback method for generic Pyomo Variables """ 
        initializeGenericPyomoVariables(self, pM)




#%%


class SourceSink(Component):

    def get_variable_cost(self, pM):
        # time should be sourced from the LESO.System class to enforce time sync.
        time = pM.time
        flow = np.array([self.state.power[t] for t in time])
        fee = np.where(flow>0, self.variable_cost, self.variable_income)
        cost_array = flow * fee

        return float(sum(cost_array)) * self.pyoVar

    pass


class Storage(Component):
    def power_control(self):
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
    states = ["power"]

    def __init__(self, name, **kwargs):

        # Set default values as instance attribute
        self.default()
        # Let custom component setter handle the custom values
        self.custom(**kwargs)



        PhotoVoltaic.instances += 1
        self.number = PhotoVoltaic.instances
        self.name = name

    @property
    def area(self):
        return self.installed / self.module_power * self.module_area

    @area.setter
    def area(self, value):
        return print(
            "---> Note: Change the module power or -area to change this variable"
        )

    @property
    def opex(self):
        try:
            opex = self._opex
        except AttributeError:
            opex = self.capex * self.opex_ratio
        return opex
        
    @opex.setter
    def opex(self, value):
        self._opex = value
    
    def __str__(self):
        return "pv{number}".format(number=self.number)

    def calculate_time_serie(self, tmy):

        if self.use_ninja:
            self.state.power = feedinfunctions.ninja_PVpower(self, tmy) # TODO
        else:
            self.state.power = feedinfunctions.PVpower(self, tmy)

class PhotoVoltaicAdvanced(SourceSink):

    instances = 0

    # read default values
    default_values = defs.pva
    states = ["power"]

    def __init__(self, name, **kwargs):

        # Set default values as instance attribute
        self.default()
        # Let custom component setter handle the custom values
        self.custom(**kwargs)



        PhotoVoltaicAdvanced.instances += 1
        self.number = PhotoVoltaicAdvanced.instances
        self.name = name

    def __str__(self):
        return "pva{number}".format(number=self.number)

    def calculate_time_serie(self, tmy):

        self.state.power = feedinfunctions.PVlibwrapper(self, tmy)

class BifacialPhotoVoltaic(SourceSink):

    instances = 0

    # read default values
    default_values = defs.pvb
    states = ["power"]

    def __init__(self, name, **kwargs):

        # Set default values as instance attribute
        self.default()
        # Let custom component setter handle the custom values
        self.custom(**kwargs)



        BifacialPhotoVoltaic.instances += 1
        self.number = BifacialPhotoVoltaic.instances
        self.name = name

    def __str__(self):
        return "pv-bi{number}".format(number=self.number)

    def calculate_time_serie(self, tmy):
        
        self.bifacial_irradiance = feedinfunctions.bifacial(self, tmy)
        self.state.power = feedinfunctions.PVlibwrapper(self, tmy)


class FinalBalance(SourceSink):

    # read default values
    default_values = defs.finalbalance
    states = ["power"]
    control_states = {"power": 1}

    def __init__(self, **kwargs):
        
        name = kwargs.pop("name", None)
        if name:
            self.name = name
        else:
            self.name = self.__str__()

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)

        
    def __str__(self):
        return "FinalBalance"

    def power_control(self, balance_in):

        from LESO.scenario.balancing import final_power_control

        self.state.power = final_power_control(balance_in)

    def construct_constraints(self, system):

        core.final_balance_power_control_constraints(system.model, self)


class Wind(SourceSink):

    instances = 0
    default_values = defs.wind
    states = ["power"]

    def __init__(self, name, lat=53, lon=6, height=100, **kwargs):

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)


        # fetch own tmy set
        if self.use_dowa:
            self.dowa = get_dowa(lat, lon, height=height)

        Wind.instances += 1
        self.number = Wind.instances
        self.name = name
    
    @property
    def opex(self):
        try:
            opex = self._opex
        except AttributeError:
            opex = self.capex * self.opex_ratio
        return opex
        
    @opex.setter
    def opex(self, value):
        self._opex = value
    
    def __str__(self):
        return "wind{number}".format(number=self.number)

    def calculate_time_serie(self, tmy):
        if self.use_dowa:
            self.state.power = feedinfunctions.windpower(self, self.dowa)
        elif self.use_ninja:
            self.state.power = feedinfunctions.ninja_windpower(self, tmy) # TODO
        else:
            self.state.power = feedinfunctions.windpower(self, tmy)

class WindOffshore(SourceSink):

    instances = 0
    default_values = defs.windoffshore
    states = ["power"]

    def __init__(self, name, lat=53, lon=6, height=100, **kwargs):

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)


        # fetch own tmy set
        self.dowa = get_dowa(lat, lon, height=height)
        

        WindOffshore.instances += 1
        self.number = WindOffshore.instances
        self.name = name

    def __str__(self):
        return "windoffshore{number}".format(number=self.number)

    def calculate_time_serie(self, tmy):
        # accepts but ignores system tmy
        self.state.power = feedinfunctions.windpower(self, self.dowa)

class Lithium(Storage):

    instances = 0
    default_values = defs.lithium
    states = ["power", "energy"]
    control_states = {"power": 1, "energy": 1}

    def __init__(self, name, **kwargs):

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)


        Lithium.instances += 1
        self.number = Lithium.instances
        self.name = name

    @property
    def dischargepower(self):
        return self.installed / self.EP_ratio

    @dischargepower.setter
    def dischargepower(self, value):
        return print("---> Note: Change the EP ratio to change this variable")

    @property
    def capex(self):
        cpxs = self.capex_storage
        cpxp = self.capex_power
        epr = self.EP_ratio
        return (cpxs*epr + cpxp)/epr
    
    @property
    def opex(self):
        try:
            opex = self._opex
        except AttributeError:
            opex = self.capex * self.EP_ratio * self.opex_ratio
        return opex
    
    @opex.setter
    def opex(self, value):
        self._opex = value
        
    def __str__(self):
        return f"lithium{self.EP_ratio}h_{self.number}"

    def power_control(self, balance_in):

        from LESO.scenario.balancing import battery_power_control

        [self.state.power, self.state.energy] = battery_power_control(self, balance_in)

    def construct_constraints(self, system):

        core.battery_control_constraints(system.model, self)

    def get_variable_cost(self, pM):
        time = pM.time
        key = self.__str__()
        zeros = np.zeros(len(time))
        
        # get pyoVar if key exists, otherwise zeros matrix
        P = getattr(pM, key+'_P', zeros)
        
        # returns some quadratic formula that simulates battery wear
        return sum((P[t])**2*self.variable_cost for t in time)

class Hydrogen(Storage):

    instances = 0
    default_values = defs.hydrogen
    states = ["power", "energy"]
    control_states = {"power": 1, "energy": 1}

    def __init__(self, name, **kwargs):

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)


        Hydrogen.instances += 1
        self.number = Hydrogen.instances
        self.name = name

    @property
    def dischargepower(self):
        return self.installed / self.EP_ratio

    @dischargepower.setter
    def dischargepower(self, value):
        return print("---> Note: Change the EP ratio to change this variable")

    @property
    def capex(self):
        cpx = self._capex 
        cpxr = self.capex_EP_ratio
        epr = self.EP_ratio
        return cpx * (1-cpxr)/epr + cpx*cpxr
    
    @capex.setter
    def capex(self, value):
        self._capex = value
        
    def __str__(self):
        return "hydrogen{number}".format(number=self.number)

    def power_control(self, balance_in):

        from LESO.scenario.balancing import battery_power_control

        [self.state.power, self.state.energy] = battery_power_control(self, balance_in)

    def construct_constraints(self, system):

        core.battery_control_constraints(system.model, self)
    
    def get_variable_cost(self, pM):
        time = pM.time
        key = self.__str__()
        zeros = np.zeros(len(time))
        
        # get pyoVar if key exists, otherwise zeros matrix
        P = getattr(pM, key+'_P', zeros)
        
        # returns some quadratic formula that simulates battery wear
        return sum((P[t])**2*self.variable_cost for t in time)

class FastCharger(SourceSink):

    instances = 0
    default_values = defs.fastcharger
    states = ["power"]

    def __init__(self, name, **kwargs):

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)


        FastCharger.instances += 1
        self.number = FastCharger.instances
        self.name = name
        warnings.warn(
            "Fastcharger has financial assumptions that do not scale: "
            + "please check .capex and .EV_charge_amount"
        )

    def __str__(self):
        return "fastcharger{number}".format(number=self.number)

    def calculate_time_serie(self, *args):
        self.state.power = functions.calculate_charging_demand(self)


class Consumer(SourceSink):

    instances = 0
    default_values = defs.consumer
    states = ["power"]

    def __init__(self, name, **kwargs):

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)


        Consumer.instances += 1
        self.number = Consumer.instances
        self.name = name

    def __str__(self):
        return "consumer{number}".format(number=self.number)

    def calculate_time_serie(self, *args):

        self.state.power = functions.read_consumption_profile(self)

class ETMdemand(SourceSink):

    instances = 0
    default_values = defs.etmdemand
    states = ["power"]

    def __init__(self, name, scenario_id, **kwargs):

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)

        ETMdemand.instances += 1
        self.number = ETMdemand.instances
        self.name = name

        self.scenario_id = scenario_id


    @property
    def scenario_id(self):
        return self._scenario_id

    @scenario_id.setter
    def scenario_id(self, value):
        self._scenario_id = etm_id_extractor_external(self, value)

    def __str__(self):
        return "ETMdemand{number}".format(number=self.number)

    def calculate_time_serie(self, *args):

        self.state.power = feedinfunctions.get_etm_curve(self, self.scenario_id)

class Grid(SourceSink):

    instances = 0
    default_values = defs.grid
    states = ["power"]
    control_states = {"power": 1}

    def __init__(self, name, **kwargs):

        # Set default values as instance attribute
        self.default()

        # Let custom component setter handle the custom values
        self.custom(**kwargs)


        Grid.instances += 1
        self.number = Grid.instances
        self.name = name

    def __str__(self):
        return "grid{number}".format(number=self.number)

    def power_control(self, balance_in):

        from LESO.scenario.balancing import grid_power_control

        self.state.power = grid_power_control(self, balance_in)
    
    def get_variable_cost(self, pM):
        
        time = pM.time
        ckey = self.__str__()
        power = self.state.power
        
        neg = getattr(pM, ckey+'_Pneg', 1)
        pos = getattr(pM, ckey+'_Ppos', 1)

        try:
            self.variable_income = list(self.variable_income)
        except TypeError:
            self.variable_income = [self.variable_income]*len(time)
        try:
            self.variable_cost = list(self.variable_cost)
        except TypeError:
            self.variable_cost = [self.variable_cost]*len(time)
        
        if neg == 1 and pos == 1:
            income = sum(
                power[t]*self.variable_income[t]
                if power[t] < 0
                else 0
                for t in time
            )
            cost = sum(
                power[t]*self.variable_cost[t]
                if power[t] > 0
                else 0
                for t in time
            )

        else:
            income = sum(
                neg[t]*self.variable_income[t]
                for t in time
            )
            cost = sum(
                pos[t]*self.variable_cost[t]
                for t in time
            )

        return cost + income

    def construct_constraints(self, system):

        core.direct_power_control_constraints(system.model, self)


ComponentClasses = {
    "PV system": PhotoVoltaic,
    "Wind turbine": Wind,
    "Lithium-ion ESS": Lithium,
    "DC fastcharger": FastCharger,
    "Electric consumer": Consumer,
    "Grid connection": Grid,
    "Curtailment/underload": FinalBalance,
}
