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

# ==================================Components=============================== #
styling = {
# Sinks
'label': 'Battery SOC',
'color': '#f25c5c',
'group': 'normalized'
    }

dump = dict(
        # Merit order 
        merit_tag = 'Dump',
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
        curtail = True,
        underload = False,
        # optimizer
        lower = lower_bound,          # lower bound
        upper = upper_bound,          # upper bound
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
        installed = 1200e3,           # Total power of the PV system in terms of DC       !DOF!
        azimuth = 180,                # Module orientation, N = 0                         !DOF!
        tilt = 15,                    # Optimum angle for max production                  !DOF!
        efficiency = .145,            # Total system efficiency to reach realistic values
        module_power = 325,           # STC
        module_area = 1.6,            # [m2]
        cost = 0.6,                   # total costs in euros per watt installed
        om = 5e-3,                    # e-3   €/kWp/year    OM cost
        # unused
        t_coeff = -.37,               # [%/K]
        voc = 52,                     # [V]
        isc = 30,                     # [A]
        # optimizer
        lower = 0,          # lower bound
        upper = upper_bound,          # upper bound
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
        installed = 600e3,          # total wind power installed [W]
        cost = 2.8,                 # total cost in euros per watt installed [€/W]
        om = 12e-3,                 # OM cost per year per power [€/kWp/year]  
        hubheight = 120,            # h_hub hub height [m]
        roughness = 0.25,           # z0 roughness length [m]
        # optimizer
        lower = 0,
        upper = upper_bound,
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
        price = 15e-5,           # e-5 = cents per kWh
        # styling
        
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
        # specs
        installed = 200e3,       # grid connection
        price = 25e-6,           # e-6 = euros per MWh          INCOME of export
        cost = 12.5e-5,          # e-5 = cents per kWh          COST of import
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
        cost = 280e-3,           # total cost in euros per watthours installed
        startingSOC = .7,        # Starting SOC
        cycles = 1000,           # Maximum hardcycles for life time
        discharge_hurt = 0.7,    # Maximum discharge power before the hurt
        om = 8e-3,               # e-3   €/kWp/year    OM cost
        # optimizer
        lower = 0,
        upper = upper_bound,
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
        price = 35e-5,           # e-5 = cents per kWh
        cost = 65e3,             # Euros per carger DC fast charging unit
        # related to EV 
        EV_battery = 24e3,         # e3 = kWh
        EV_consumption = 20e1,     # e1 = kWh/100km
        # optimizer
        lower = 0,
        upper = 6,
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
    "Dump": 4,    
    }










