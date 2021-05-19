"""
Default value vault
    contains the default values to run the main code
"""
# Often-used variables
lower_bound = -1e7
upper_bound = 1e7


# Used to create an empty state data-frame in every component
states = [
    'power', 
    'energy', 
    'mh2',
    ]

# Actually an arbitraty date, as long as it is in the future and starts on the
# first day of the year
start_date = '01/01/2022'

# Financial variables that govern the whole system
interest = 0.04
exp_inflation_rate = 0.015

# ==================================Components=============================== #
finalbalance = dict(
        # Merit order 
        merit_tag = 'finalbalance',
        styling = [
        {
            'label': 'Underload', 
            'color': '#f25c5c',
            'group': 'power',
        },
        {
            'label': 'Curtailment',
            'color': '#454545',
            'group': 'load',
        }],
        # settings
        dof = False,
        negative = True,  # Curtail
        positive = False, # Underload
        # optimizer
        lower = lower_bound,          # lower bound
        upper = upper_bound,          # upper bound
        # financials
        lifetime = None,
        capex = 0,
        opex = 0,
        variable_cost = 0,
        variable_income = 0,
        interest = interest,
        exp_inflation_rate = exp_inflation_rate,
    )

pv = dict(
        # Merit order 
        merit_tag = 'VRE',
        styling = {
        'label': 'PV power', 
        'color': '#ebd25b',
        'group': 'power',
        },
        # transform
        dof = False,
        installed = 1200e3,           # Total power of the PV system in terms of DC       !DOF!
        azimuth = 180,                # Module orientation, N = 0                         !DOF!
        tilt = 15,                    # Optimum angle for max production                  !DOF!
        efficiency = .145,            # Total system efficiency to reach realistic values
        module_power = 325,           # STC
        module_area = 1.6,            # [m2]
        # unused
        t_coeff = -.37,               # [%/K]
        voc = 52,                     # [V]
        isc = 30,                     # [A]
        # optimizer
        lower = 0,          # lower bound
        upper = upper_bound,          # upper bound
        # financials
        lifetime = 25,
        capex = 0.6,
        opex = 5e-3,
        variable_cost = 0,
        variable_income = 0,
        interest = 0.02,
        exp_inflation_rate = exp_inflation_rate,
    )

wind = dict(
        # Merit order 
        merit_tag = 'VRE',
        styling = {
        'label': 'Wind power', 
        'color': '#8cc0ed',
        'group': 'power',
        },
        # transform
        dof = False,
        installed = 600e3,          # total wind power installed [W]
        hubheight = 120,            # h_hub hub height [m]
        roughness = 0.25,           # z0 roughness length [m]
        # optimizer
        lower = 0,
        upper = upper_bound,
        # financials
        lifetime = 20,
        capex = 2.8,
        opex = 12e-3,
        variable_cost = 0,
        variable_income = 0,
        interest = 0.04,
        exp_inflation_rate = exp_inflation_rate,
    )

consumer = dict(
        # Merit order 
        styling = {
        'label': 'Consumption load', 
        'color': '#f5645f',
        'group': 'load',
        },
        merit_tag = 'MM',
        # transform
        scaler = 40000e3,        # e3 = kWh
        # optimizer
        dof = False,
        upper = upper_bound,
        lower = lower_bound,
        # financials
        lifetime = None,
        capex = 0,
        opex = 0,
        variable_cost = 0,
        variable_income = 15e-5,
        interest = interest,
        exp_inflation_rate = exp_inflation_rate,   
    )


grid = dict(
        # Merit order 
        merit_tag = 'Grid',
        styling = [
        {
            'label': 'Grid import', 
            'color': '#f2b65c',
            'group': 'power',
        },
        {
            'label': 'Grid export',
            'color': '#d18426',
            'group': 'load',
        }],
        # settings
        dof = False,
        negative = True,    # Import
        positive = True,    # Export
        upper = upper_bound,
        lower = lower_bound,
        # specs
        installed = 200e3,       # grid connection
        # financials
        lifetime = None,
        capex = 0,
        opex = 0,
        variable_cost = 12.5e-5,
        variable_income = 25e-6,
        interest = interest,
        exp_inflation_rate = exp_inflation_rate,
    )


lithium = dict(
        # Merit order 
        merit_tag = 'ESS',
        styling = [
        {
            'label': 'Battery discharging', 
            'color': '#7fc78f',
            'group': 'power',
        },
        {
            'label': 'Battery charging',
            'color': '#85a0d6',
            'group': 'load',
        },
        {
            'label': 'Battery energy', 
            'color': '#85a0d6',
            'group': 'energy',
        }],
        # specs
        installed = 1000e3,      # 1000 kWh installed capacity
        EP_ratio = 1.25,         # ratio of energy to power
        startingSOC = .7,        # Starting SOC
        cycles = 1000,           # Maximum hardcycles for life time
        discharge_hurt = 0.7,    # Maximum discharge power before the hurt
        # optimizer
        dof = False,
        lower = 0,
        positive = True,
        negative = True,
        upper = upper_bound,
        # financials
        lifetime = 10,
        capex = 280e-3,
        opex = 8e-3,
        variable_cost = 2.8e-9,
        variable_income = 2.8e-9,
        interest = interest,
        exp_inflation_rate = exp_inflation_rate,
    )

fastcharger = dict(
        # Merit order 
        merit_tag = 'MM',
        styling = {
        'label': 'Charging load',
        'color': '#a5c0c2',
        'group': 'load',
        },
        installed = 4,           # 4 chargers
        maxpower = 150e3,        # maximum charger power (change CARSPERHOUR)
        carsperhour = 4,         # Change MANUALLY based on ^^^ !!!
        efficiency = 0.85,       # DC fast charging reference
        # related to EV 
        EV_battery = 24e3,         # e3 = kWh
        EV_consumption = 20e1,     # e1 = kWh/100km
        # optimizer
        dof = False,
        lower = 0,
        upper = 6,
        # financials
        lifetime = 15,
        capex = 65e3,
        opex = 0,
        variable_cost = 0,
        variable_income = 35e-5,
        interest = interest,
        exp_inflation_rate = exp_inflation_rate,
    )


# ==================================Auxiliaries============================== #

""" 
--> Merit order
    Basic interpertation for defining the order of the elements on various levels 
    of the merit order balance.

    --> dict with key-value pairs
        
        key: str, corresponding to the component.merit_order attribute
        value: level on the merit order of that component
        
        
    + Abreviation   | Meaning                       | Existing components
    ------------------------------------------------|------------------- 
    + VRE           | Volatile Renewable Energy     | (PhotoVoltaic, Wind)
    + MM            | Must meet loads               | (Consumption, Charger)
    + ESS           | Electric storage system       | (Lithium)     
    + GRD           | Grid                          | (Grid)


    Use value 0 if not applicable in model scope.

    + DRE           | Dispatchable RE               | e.g. hydro / biomass?

"""


merit_order = {
    "VRE" : 1,
    "DRE" : 0,
    "MM" : 1,
    "ESS" : 2,
    "Grid" : 3,
    "finalbalance": 4,    
    }




