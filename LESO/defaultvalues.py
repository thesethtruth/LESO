"""
Default value vault
    contains the default values to run the main code
"""
from copy import deepcopy as copy

# Often-used variables
lower_bound = -1e7
upper_bound = 1e7
system_lifetime = 25

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
        installed = 5000e3,           # [..W] total installed capacity 
        azimuth = 180,                # [degree] Module orientation
        tilt = 15,                    # [degree] Tilt of plane relative to horizontal 
        efficiency = .185,            # [-] Total system efficiency to reach realistic values
        module_power = 350,           # [w] output power under STC
        module_area = 1.6,            # [m2] module area
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
        opex_ratio = 0.0015, #% based on ETRI2014
        variable_cost = 0,
        variable_income = 0,
        interest = 0.02,
        exp_inflation_rate = exp_inflation_rate,
        # options for using renewable ninja
        use_ninja = False,
        date_from ='2015-01-01',
        date_to = '2015-12-31',
        dataset = 'merra2',
    )

pva = dict(
        # Merit order 
        merit_tag = 'VRE',
        styling = {
        'label': 'PV power', 
        'color': '#ebd25b',
        'group': 'power',
        },
        # transform
        dof = False,
        installed = 5000e3,           # Total power of the PV system in terms of DC       !DOF!
        azimuth = 180,                # Module orientation, N = 0                         !DOF!
        tilt = 15,                    # Optimum angle for max production                  !DOF!
        tracking = False,
        
        # browse CEC files using pvlib to change the system
        module = 'Jinko_Solar_Co___Ltd_JKM350M_72_V',
        inverter = 'Huawei_Technologies_Co___Ltd___SUN2000_100KTL_USH0__800V_',
        strings_per_inverter = 12,
        modules_per_string = 32,
        # optimizer
        lower = 0,                    # lower bound
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

pvb = dict(
        # Merit order 
        merit_tag = 'VRE',
        styling = {
        'label': 'Bifacial PV power', 
        'color': '#ebd25b',
        'group': 'power',
        },
        # transform
        dof = False,
        installed = 5000e3,           # Total power of the PV system in terms of DC       !DOF!
        azimuth = 180,                # Module orientation, N = 0                         !DOF!
        tilt = 15,                    # Optimum angle for max production
        tracking = False,                  
        # browse CEC files using pvlib to change the system
        module = 'Jinko_Solar_Co___Ltd_JKM350M_72_V',
        inverter = 'Huawei_Technologies_Co___Ltd___SUN2000_100KTL_USH0__800V_',
        strings_per_inverter = 12,
        modules_per_string = 28,
        bifacial_factor = 0.8,
        # optimizer
        lower = 0,                    # lower bound
        upper = upper_bound,          # upper bound
        # financials
        lifetime = 25,
        capex = 0.75,
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
        roughness = 0.25,           # z0 roughness length [m]
        turbine_type = "E-126/4200",  # turbine type as in oedb turbine library
        hub_height = 135,  # in m
        # data source
        use_dowa = False,
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
        # options for using renewable ninja
        use_ninja = False,
        date_from ='2015-01-01',
        date_to = '2015-12-31',
        dataset = 'merra2',
)

windoffshore = dict(
        # Merit order 
        merit_tag = 'VRE',
        styling = {
        'label': 'Offshore wind power', 
        'color': '#8cc0ed',
        'group': 'power',
        },
        # transform
        dof = False,
        installed = 600e3,              # total wind power installed [W]
        hubheight = 120,                # h_hub hub height [m]
        roughness = 0.0002,             # z0 roughness length [m]
        transport_efficiency = .92,         # from turbine to location
        # optimizer
        lower = 0,
        upper = upper_bound,
        # financials
        lifetime = 20,
        capex = wind['capex']*1.2,      # 20% higher
        opex = wind['opex']*1.4,        # 40% higher
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

etmdemand = dict(
        # Merit order 
        styling = {
        'label': 'Consumption load', 
        'color': '#f5645f',
        'group': 'load',
        },
        merit_tag = 'MM',
        # specs
        generation_whitelist = False,
        # optimizer
        dof = False,
        upper = upper_bound,
        lower = lower_bound,
        # financials
        lifetime = None,
        capex = 0,
        opex = 0,
        variable_cost = 0,
        variable_income = 0,
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
        variable_cost = 125e-6,
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
        installed = 1,              # 1000 kWh installed capacity
        EP_ratio = 2,               # Energy to power ratio ; duration of storage
        startingSOC = .7,           # Starting SOC
        discharge_rate = 0.9995,    # hourly discharge
        cycle_efficieny = .85,      # cite: ATB NPREL
        # optimizer
        dof = False,
        lower = 0,
        positive = True,
        negative = True,
        upper = upper_bound,
        # financials
        lifetime = 15,              # cite: ATB NPREL
        capex_storage = 277e-3,     # cite: ATB NPREL
        capex_power = 257e-3,       # part of component cost related to storage only
        opex = 2.5e-2,              # [%] cite: ATB NPREL (fraction of TOTAL cost)
        variable_cost = 2.8e-12,
        variable_income = 2.8e-12,
        interest = interest,
        exp_inflation_rate = exp_inflation_rate,
    )

hydrogen = dict(
        # Merit order 
        merit_tag = 'H2',
        styling = [
        {
            'label': 'H2 fuelcell power', 
            'color': '#46b3af',
            'group': 'power',
        },
        {
            'label': 'H2 electrolyser load',
            'color': '#ba5db1',
            'group': 'load',
        },
        {
            'label': 'H2 storage energy', 
            'color': '#85a0d6',
            'group': 'energy',
        }],
        # specs
        installed = 1000e3,      # 1000 kWh installed capacity
        EP_ratio = 50,         # ratio of energy to power (influences component cost)
        startingSOC = .1,        # Starting SOC
        discharge_rate = 1,   # hourly discharge
        cycle_efficieny = 0.45,  # round trip efficiency
        # optimizer
        dof = False,
        lower = 0,
        positive = True,
        negative = True,
        upper = upper_bound,
        # financials
        lifetime = 15,
        capex = 2607e-3,             # capex at EP = 1
        capex_EP_ratio = .0055,       # part of component cost related to storage only at EP = 1
        opex = 8e-3,
        variable_cost = 2.8e-12,
        variable_income = 2.8e-12,
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
    "H2": 2,
    "Grid" : 3,
    "finalbalance": 4,    
    }

scenarios_gelderland = { 
    '2030Gelderland_hoog': {'id': 815715, 'latlon': (52, 6)},
    '2030Gelderland_laag': {'id': 815716, 'latlon': (52, 6)},
    '2030RES_Achterhoek': {'id': 815753, 'latlon': (52, 6.4)},
    '2030RES_ArnhemNijmegen': {'id': 815754, 'latlon': (54.9, 5.9)},
    '2030RES_Cleantech': {'id': 815755, 'latlon': (52.2, 6.1)},
    '2030RES_Foodvalley ': {'id': 815756, 'latlon': (52.1, 5.7)},
    '2030RES_NoordVeluwe': {'id': 815757, 'latlon': (52.4, 5.8)},
    '2030RES_Rivierenland': {'id': 815758, 'latlon': (51.9, 5.3)},
} 

generation_whitelist = [
    'buildings_solar_pv_solar_radiation.output (MW)',
    'energy_chp_combined_cycle_network_gas.output (MW)',
    'energy_chp_local_engine_biogas.output (MW)',
    'energy_chp_local_engine_network_gas.output (MW)',
    'energy_chp_local_wood_pellets.output (MW)',
    'energy_chp_supercritical_waste_mix.output (MW)',
    'energy_flexibility_curtailment_electricity.output (MW)',
    'energy_flexibility_hv_opac_electricity.output (MW)',
    'energy_flexibility_mv_batteries_electricity.output (MW)',
    'energy_flexibility_pumped_storage_electricity.output (MW)',
    'energy_heat_flexibility_p2h_boiler_electricity.output (MW)',
    'energy_heat_flexibility_p2h_heatpump_electricity.output (MW)',
    'energy_hydrogen_flexibility_p2g_electricity.output (MW)',
    'energy_power_combined_cycle_hydrogen.output (MW)',
    'energy_power_geothermal.output (MW)',
    'energy_power_hydro_mountain.output (MW)',
    'energy_power_hydro_river.output (MW)',
    'energy_power_nuclear_gen2_uranium_oxide.output (MW)',
    'energy_power_nuclear_gen3_uranium_oxide.output (MW)',
    'energy_power_solar_csp_solar_radiation.output (MW)',
    'energy_power_solar_pv_solar_radiation.output (MW)',
    'energy_power_supercritical_waste_mix.output (MW)',
    'energy_power_turbine_hydrogen.output (MW)',
    'energy_power_wind_turbine_coastal.output (MW)',
    'energy_power_wind_turbine_inland.output (MW)',
    'energy_power_wind_turbine_offshore.output (MW)',
    'households_flexibility_p2p_electricity.output (MW)',
    'households_solar_pv_solar_radiation.output (MW)',
    'industry_chemicals_other_flexibility_p2h_hydrogen_electricity.output (MW)',
    'industry_chemicals_refineries_flexibility_p2h_hydrogen_electricity.output (MW)',
    'industry_other_food_flexibility_p2h_hydrogen_electricity.output (MW)',
    'industry_other_paper_flexibility_p2h_hydrogen_electricity.output (MW)',
    'transport_car_flexibility_p2p_electricity.output (MW)',
]
