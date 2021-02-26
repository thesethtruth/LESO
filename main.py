import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os.path
import feedinfunctions
import API
plt.close('all')

# coordinates of central Netherlands (~Utrecht)
lat, lon = 52, 5

# DOF options
batterysize = 2e6   #1e6 = MWh 
chargers = 4

span = False
if span: 
    
    # battery span
    battery_min = 0
    battery_step = 100e3         #1e3 = kWh
    battery_span = np.arange(battery_min, batterysize+battery_step, battery_step)
    
    # charger span
    chargers_min = 1
    chargers_span = np.arange(chargers_min, chargers+1)
    
      
# printing options
storedata = True
performancedata = True
printme = False
logme = False




# Set up user constants -------------------------------------------------------
start_future = '1/1/2021'   # Starting date of the future simulation


#%% sytem input variables

class PV:
    pass
PV.installed = 1200e3           # Total power of the PV system in terms of DC       !DOF!
PV.azimuth = 180                # Module orientation, N = 0                         !DOF!
PV.tilt = 80                    # Optimum angle for max production                  !DOF!
PV.efficiency = .145            # Total system efficiency to reach realistic values
PV.module_power = 325                 # STC
PV.module_area = 1.6                  # [m2]
PV.area = PV.installed/PV.module_power*PV.module_area
PV.cost = 0.6                   # total costs in euros per watt installed
PV.om = 5e-3                    # e-3   €/kWp/year    OM cost

# unused
PV.t_coeff = -.37              # [%/K]
PV.voc = 52                    # [V]
PV.isc = 30                    # [A]

class wind:
    pass
wind.installed = 600e3          # total wind power installed [W]
wind.cost = 2.8                 # total cost in euros per watt installed [€/W]
wind.om = 12e-3                 # OM cost per year per power [€/kWp/year]  
wind.hubheight = 120            # h_hub hub height [m]
wind.roughness = 0.25           # z0 roughness length [m]


class consumption:
    pass
consumption.scaler = 40000e3        # e3 = kWh
consumption.price = 15e-5           # e-5 = cents per kWh

class grid:
    pass
grid.installed = 200e3       # grid connection
grid.price = 25e-6           # e-6 = euros per MWh          INCOME of export
grid.cost = 12.5e-5            # e-5 = cents per kWh          COST of import

class battery:
    pass

battery.EP_ratio = 1.25         # ratio of energy to power

battery.cost = 280e-3           # total cost in euros per watthours installed
battery.startingSOC = .7        # Starting SOC
battery.cycles = 1000           # Maximum hardcycles for life time
battery.discharge_hurt = 0.7    # Maximum discharge power before the hurt
battery.om = 8e-3               # e-3   €/kWp/year    OM cost

class charger:
    pass

charger.maxpower = 150e3           # maximum charger power (change CARSPERHOUR)
charger.carsperhour = 4         # Change MANUALLY based on ^^^ !!!
charger.efficiency = 0.85       # DC fast charging reference
charger.price = 35e-5           # e-5 = cents per kWh
charger.cost = 65e3             # Euros per carger DC fast charging unit

class EV:
    pass
EV.battery = 24e3       # e3 = kWh
EV.consumption = 20e1   # e1 = kWh/100km

   
#%% time series

#   1 --- TMY
"""
fetch TMY data using PVGIS API chain
Converts .json respons to dataframe. Appends tmy-info as attributes to 'tmy'.
e.g. tmy.lat gives the lattitude used for this tmy set. 
"""
tmy = API.get(lat, lon)

#   2 --- wind
""" 
Calculate wind power series using a custom windpowerlib model chain based on 
TMY data. Appends generation time serie as attribute 'power' to 'wind' class.
""" 
wind = feedinfunctions.windpower(wind, tmy)     # U

#   3 --- PV
"""
Calculate PV power series using a custom pvlib model chain based on
TMY data. Appends generation time serie as attribute 'power' to 'PV' class.
""" 
PV = feedinfunctions.PVpower(PV, tmy)

#   4 --- Consumption
"""
Imports a certain profile (industrial as in current setings) from NEDU data.
"""
from functions import Consumptionf
dataset_location = "data/consumption.csv"
consumption = Consumptionf(start_future, consumption, dataset_location)


#%%
# Here we assign the external values (such that we save some computing time)
computed_all = False
chargtick = 0
batterytick = -1
while not computed_all:
    
    # calculate the range
    if span:
        
        if batterytick == len(battery_span):
            chargtick += 1
            batterytick = 0
        
        charger.installed = chargers_span[chargtick]
        battery.installed = battery_span[batterytick]
        batterytick += 1
             
        # print("This loops {} chargers".format(charger.installed), 
        #      " & ", "a {} kWh battery".format(battery.installed/1e3))
     
    # single instance calculation
    else:
        charger.installed = chargers            # amount of chargers
        battery.installed = batterysize         # batterysize
        

                
    #%%
    # and the dependent variable
    battery.dischargepower = battery.installed / battery.EP_ratio          # W
    
    
    
    
    
    
    # EV charging
    from functions import Chargerf
    EV_dataset_location = 'data/EV_charge.pkl'
    charger, EV = Chargerf(charger, EV, EV_dataset_location)
    
    
    
    
     
    
    #%% conversion steps
        
    class balance():
        pass
    
    # ---- 
    # balance.one == loads vs power
    totalload = charger.load + consumption.load
    totalpower = PV.power + wind.power
    #                                                                                       CHECK THIS
    
    balance.one = PV.power \
                + wind.power \
                + consumption.load \
                + charger.load
      
    balance.yearly = wind.yearly + PV.yearly + consumption.yearly + charger.yearly
    
    # balance.two == put to sink what we can, given maximum power, capacity and current SOC
    # -----> [e.g. battery.dischargepower, battery.installed and battery.sink.SOC]
    
    from functions import BatteryControlf
    battery = BatteryControlf(start_future, balance, battery) 
    
    balance.two = balance.one + battery.power + battery.load
    
    # ----
    # balance.three == grid import [grid.power] and grid export [grid.load]
        # NOTE: import when balance is negative, such that power (import) is positive
        # NOTE2: export when balance is positive, such that load (export) is negative
        # THUS; grid variables are inversely postive/negative w.r.t. balance
    
    # IMPORT
    # where balance is negative, we will import
    grid.power = -balance.two.where( balance.two<0 , 0.0)
    # where import is greater than grid capacity, we cap to grid capacity
    grid.power = grid.power.mask( grid.power > grid.installed , grid.installed)
    
    # EXPORT
    # where balance is positive, we will export 
    grid.load = -balance.two.where( balance.two > 0, 0.0)
    # where export is greater than grid capacity, we cap to grid capacity
    grid.load = grid.load.mask( grid.load < -grid.installed, -grid.installed)
    
    
    # formulate balance after import / export
    balance.three = balance.two + grid.load + grid.power
    
    # ----
    # balance.underloaded / balance.curtailed == final balance with remainders
    
    balance.underloaded = -balance.three.where(balance.three < 0, 0.0)
    balance.curtailed = -balance.three.where(balance.three > 0, 0.0)
    balance.net = balance.curtailed + balance.underloaded
    
    #%% Troubleshooting
    troubleshooting = False
    if troubleshooting:
        plt.figure()
        balance.one.plot(label='rough balance')
        balance.two.plot(label='after battery')
        balance.three.plot(label='three')
        plt.legend()
        
        print("Balance one:   {:.1f} MWh".format(balance.one.sum()/1e6))
        print("Balance two:   {:.1f} MWh".format(balance.two.sum()/1e6))
        print("Balance three: {:.1f} MWh".format(balance.three.sum()/1e6))
    
    # == Mental note to self, consider below: ==
    
    # -- Merit order of power
    # PV.power
    # wind.power
    # battery.power
    # grid.power
    # balance.underloaded
    
    # -- Merit order of loads
    # consumption.load
    # charger.load
    # grid.load
    # battery.load
    # balance.curtalied
    
    # -- Merit order of sinks
    # battery.sink
    
    # ===========================================
    
    # import
    grid.power.hours = np.where(grid.power > 0, True, False).sum()
    grid.power.yearly = grid.power.sum()
    
    # underload
    balance.underloaded.hours = (~(balance.underloaded==0) ).sum()
    balance.underloaded.timepercentage = balance.underloaded.hours / 8760
    balance.underloaded.yearly = balance.underloaded.sum()
    # find a different formula for this to relatively explain it                        # change me
    balance.underloaded.energypercentage = balance.underloaded.yearly / totalload.sum()
    
    
    # export
    grid.load.hours = np.where(grid.load < 0, True, False).sum()
    grid.load.yearly = grid.load.sum()
    
    # curtailment
    balance.curtailed.hours = (~(balance.curtailed==0) ).sum()
    balance.curtailed.timepercentage = balance.curtailed.hours / 8760
    balance.curtailed.yearly = balance.curtailed.sum()
    # find a different formula for this to relatively explain it                        # change me
    balance.curtailed.energypercentage = balance.curtailed.yearly / totalpower.sum()
    
    
    # battery lifetime estimation
    battery.hardcycles = (battery.power + battery.load >= battery.discharge_hurt*battery.dischargepower).sum()
    EV.yearly_kilometers = -(charger.yearly * charger.efficiency)/EV.consumption
    
    if battery.hardcycles > 0: 
        battery.lifetime = battery.cycles / battery.hardcycles
    else:
        battery.lifetime = 99
    
    
    
    
    #%% financial section
    from functions import FinanicalFunction
    finance = FinanicalFunction(PV, wind, battery, charger, consumption, grid)
            
    #%% ---------------- Printing section ----------------------------------------
    if printme:
        from functions import PrintingFunction
        PrintingFunction(PV, wind, battery, charger, grid, balance, consumption, finance, EV, logme= logme)
    
    
    
    #%% plotting section
    
    
    
    
    # collect all data
    if storedata:
    
    # ---------------
        # finanical information to save
        
        if performancedata:
            performancedict = {
                # DOFs
                'Chargers': [charger.installed, 'units'],
                'Battery capacity': [battery.installed/1e3, 'kWh'],
                # CAPEX
                'Wind CAPEX': [wind.capex/1e3, ' x1000 € ' ],
                'PV CAPEX': [PV.capex/1e3, ' x1000 € ' ],
                'Battery CAPEX': [battery.capex/1e3, ' x1000 € ' ],
                'Chargers CAPEX': [charger.capex/1e3, ' x1000 € ' ],
                'Total CAPEX': [finance.capex/1e3, ' x1000 € ' ],
                # OPEX
                'Wind OPEX': [wind.opex/1e3, ' x1000 € / y ' ],
                'PV OPEX': [PV.opex/1e3, ' x1000 € / y ' ],
                'Battery OPEX': [battery.opex/1e3, ' x1000 € / y ' ],
                'Total OPEX': [finance.opex/1e3, ' x1000 € / y ' ],
                # income
                'Charging sales': [charger.income/1e3, ' x1000 € / y ' ],
                'Consumption sales': [consumption.income/1e3, ' x1000 € / y ' ],
                'Grid sales/cost': [grid.income/1e3, ' x1000 € / y ' ], 
                'Yearly income': [finance.income/1e3, ' x1000 € / y ' ],
                'Yearly net icome': [finance.net_income/1e3, ' x1000 € / y ' ],
                # KPIs
                'Payback period [PBY]': [finance.PBY, ' years ' ],
                'Internal Rate of Return [IRR]': [finance.IRR, ' % ' ],
                'Service coverage on yearly basis': [1 - balance.underloaded.timepercentage, ' % ' ],
                'Amount of passenger kilometers covered': [EV.yearly_kilometers/1e6, ' Million km ' ],
                'E-mobility covered': [EV.yearly_kilometers/12000, ' households ' ],
                'Times earth circumnavigated by EVs': [EV.yearly_kilometers/40075, ' times ' ],
                # design
                'Underloaded hours': [balance.underloaded.hours, ' hours ' ],
                'Underload percent of time': [balance.underloaded.timepercentage*100, ' % ' ],
                'Total energy underload': [balance.underloaded.sum()/1e6, ' MWh ' ],
                'Underload percentage of energy': [balance.underloaded.energypercentage*100, ' % ' ],
                'Yearly grid import': [grid.power.yearly/1e6, ' MWh ' ],
                'Yearly grid export': [-grid.load.yearly/1e6, ' MWh ' ],
                'Yearly curtailed energy': [-balance.curtailed.yearly/1e6, ' MWh ' ],
                'Curtailed percentage': [-balance.curtailed.energypercentage*100, ' % ' ],
        }
        
        tags = [value[1] for key, value in performancedict.items()]
        values = [value[0] for key, value in performancedict.items()]

        if os.path.isfile("outputdata/performanceindicators.pkl"):
            
            # pi file exists
            pi = pd.read_pickle("outputdata/performanceindicators.pkl")
            
            # check if option is already added
            if (pi.isin([charger.installed, battery.installed/1e3])[pi.columns[1]] & \
            pi.isin([charger.installed, battery.installed/1e3])[pi.columns[0]]).any():
                
                # take no action - if data already exists
                None
            
            # otherwise we add the configuration to the list
            else:
                
                pi2 = pd.DataFrame(columns = list(performancedict.keys()), data= [values])
                pi = pi.append(pi2)
                
                
                pi = pi.sort_values(by = ['Chargers', 'Battery capacity'])
                pi.to_pickle("outputdata/performanceindicators.pkl")
                pi.to_csv("outputdata/performanceindicators.csv")
                print("")
                print('Indicators added to indicator dataframe')
                
        
        else:
            
            # pi file DOES NOT exist
            print ("Performance indicators file does not exist! (file is now initialized)")
            pi = pd.DataFrame(columns = list(performancedict.keys()), index = ['axis tag'], data = [tags])
            pi2 = pd.DataFrame(columns = list(performancedict.keys()), data= [values])
            pi = pi.append(pi2)
            pi.to_pickle("outputdata/performanceindicators.pkl")
            pi.to_csv("outputdata/performanceindicators.csv")
            
    
    # -----------
        # time series to save
        
        timeseriesdict = {
            # Powers
            'PV power': PV.power,
            'Wind power': wind.power,
            'Battery discharging':  battery.power,
            'Grid import': grid.power,
            'Underload': balance.underloaded,
            # Loads
            'Consumption load': consumption.load,
            'Charging load': charger.load,
            'Battery charging': battery.load,
            'Grid export': grid.load,
            'Curtailment': balance.curtailed,
            # Sinks
            'Battery energy': battery.sink,
            'Battery SOC': battery.sink.SOC
        }
        
        # make DF
        timeseriesdf = pd.DataFrame()
        for keys, data in timeseriesdict.items():
            timeseriesdf[keys]=data
            
        # save DF    
        dataname = 'timeseries'
        filename = "{dataname}_{batterysize}kWh_{chargers}chargers".format(dataname= dataname, batterysize = battery.installed/1e3, chargers = charger.installed)
        timeseriesdf.to_pickle('outputdata/{filename}.pkl'.format(filename= filename))
        print("")
        print("Saved {dataname} as {filename}:".format(filename = filename, dataname = dataname))
    
    # ---------------
        # yearly series to save
        
        from functions import _Weeks
            
        yearlydict = {
            # Powers
            'PV power': PV.power.groupby(_Weeks()).sum(),
            'Wind power': wind.power.groupby(_Weeks()).sum(),
            'Battery discharging':  battery.power.groupby(_Weeks()).sum(),
            'Grid import': grid.power.groupby(_Weeks()).sum(),
            'Underload': balance.underloaded.groupby(_Weeks()).sum(),
            # Loads
            'Consumption load': consumption.load.groupby(_Weeks()).sum(),
            'Charging load': charger.load.groupby(_Weeks()).sum(),
            'Battery charging': battery.load.groupby(_Weeks()).sum(),
            'Grid export': grid.load.groupby(_Weeks()).sum(),
            'Curtailment': balance.curtailed.groupby(_Weeks()).sum(),
            # Sinks
            'Battery energy': battery.sink.groupby(_Weeks()).sum(),
            'Battery SOC': battery.sink.SOC.groupby(_Weeks()).sum()
        }
        
        # make DF
        yearlydf = pd.DataFrame()
        for keys, data in yearlydict.items():
            yearlydf[keys]=data
            
        # save DF    
        dataname = 'yearly'
        filename = "{dataname}_{batterysize}kWh_{chargers}chargers".format(dataname= dataname, batterysize = battery.installed/1e3, chargers = charger.installed)
        yearlydf.to_pickle('outputdata/{filename}.pkl'.format(filename= filename))
        print("")
        print("Saved {dataname} as {filename}:".format(filename = filename, dataname = dataname))
    
    
    # --------------
        # optionframe for Dash
        
        if os.path.isfile("outputdata/optionframe.pkl"):

            # optionframe file exists
            optionframe = pd.read_pickle("outputdata/optionframe.pkl")
        
        # check if option is already added
            if (optionframe.isin([charger.installed, battery.installed/1e3])[optionframe.columns[1]] & \
            optionframe.isin([charger.installed, battery.installed/1e3])[optionframe.columns[0]]).any():
            
                # take no action - if option already exists
                None
            
            # otherwise we add the configuration to the list
            else:
                
                # add and sort the options
                optionframe2 = pd.DataFrame(columns = ['Chargers', 'Battery capacity'], data = [list([charger.installed, battery.installed/1e3])])
                optionframe = optionframe.append(optionframe2)
                optionframe = optionframe.sort_values(by = ['Chargers', 'Battery capacity'])
                
                # save twice (one for browsing)
                optionframe.to_pickle("outputdata/optionframe.pkl")
                optionframe.to_csv("outputdata/optionframe.csv")
                
                # confirm
                print("")
                print('Options added to optionframe')
        
        
        else:
        
            # optionframe file DOES NOT exist
            optionframe = pd.DataFrame(columns = ['Chargers', 'Battery capacity'], data =[list([charger.installed, battery.installed/1e3])])

            # save twice (one for browsing) 
            optionframe.to_pickle("outputdata/optionframe.pkl")
            optionframe.to_csv("outputdata/optionframe.csv")
            
            # confirm
            print("")
            print ("Option frame does not exist! (file is now initialized)")
        



    # exit condition
    if charger.installed == chargers: 
        if battery.installed == batterysize:
            print('YEET (Le fin)')
            # exit after the final / only value is reached of both components
            computed_all = True
            break




