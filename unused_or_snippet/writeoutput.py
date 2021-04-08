import pandas as pd
import os.path


def dashpickle(PV, wind, battery, charger, consumption, EV, grid, balance, finance, performancedata_write = True):
    """
    Takes all information of a certain model calculation and saves it,
    if this instance has not yet been calculated. 
       Time series
           Weekly
           Hourly
               Corresponding option frame for populating dropdowns
        Performance indicators
                Corresponding option frame for populating dropdowns
    
   Formatting based on the way Dash dashboard uses information.
    
        Input:
            all component classes and their timeseries attributes
            performancedata_write, if false does not save the PI of the system
            
    
    """
    if performancedata_write:
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
        
    
    
    
