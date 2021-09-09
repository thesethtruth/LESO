import os
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from pathlib import Path
from scipy.stats import truncexpon

FOLDER = Path(__file__).parent


def read_consumption_profile(consumer_instance, 
                             path_to_data = "data\\consumption.csv"):
    
    consumer = consumer_instance
    
    dir = os.path.dirname(__file__)
    filepath = os.path.join(dir, path_to_data)
    print(filepath)

    # read data
    temp_consumption = pd.read_csv(filepath,
                         nrows=35040,skiprows=5,
                         usecols=[3] # change this col to change profile
                         )
    temp_consumption.columns = ["Consumption"]
    
    # Sum the data from every 15 mins to 1 hour
    temp_consumption = temp_consumption["Consumption"].groupby(temp_consumption.index // 4).sum()
    
    # Set the dates 
    temp_consumption.index = consumer.state.index
    
    # Scale the consumption to appropriate size
    power = -temp_consumption*consumer.scaler
    
    return power

def determine_chargable_ev_traffic(fastcharger):
    
    def read_csv(fp):
        return pd.read_csv(
        fp, index_col=0
        ).apply(lambda x: int(round(x)), axis=1
        ).values

    ## Read in the weekday traffic
    try:
        weekday = read_csv(fastcharger.weekday_traffic_file)
    except FileNotFoundError:
        weekday = read_csv(FOLDER / fastcharger.weekday_traffic_file)
    
    ## Read in the weekendday traffic
    try:
        weekendday = read_csv(fastcharger.weekendday_traffic_file)
    except FileNotFoundError:
        weekendday = read_csv(FOLDER / fastcharger.weekendday_traffic_file)

    # init empty series and assign the correct days based on the charger indices
    EV_charge = pd.Series(index=fastcharger.state.index, dtype=int)
    for i in range(365):
        d = i * 24
        if EV_charge.index[d].weekday()<5:
            EV_charge.iloc[d:d+24] = weekday
        else:   
            EV_charge.iloc[d:d+24] = weekendday

    # A truncated filter which is used to 'predict'/stochastically assign a soc to any vehicle
    def soc_trunc_filter(traffic, min_soc):
        socs = truncexpon.rvs(1, size=traffic, random_state=49816317) # TODO random seed might be counter productive
        should_charge = len(socs[socs < min_soc])
        return should_charge
    
    # apply the filter
    EV_traffic = EV_charge.apply(
        soc_trunc_filter, 
        args=(fastcharger.EV_min_soc,)
        )
    
    # mutliply by the EV share to
    fastcharger.EV_traffic = (EV_traffic * fastcharger.EV_share).round(0)

    return None

def calculate_charging_demand(fastcharger):
    
    # first determine the chargable ev traffic based on traffic data supplied
    determine_chargable_ev_traffic(fastcharger)

    # from the traffic, cap the actually demand to available chargers on hourly basis
    fastcharger.EV_to_chargers = fastcharger.EV_traffic.where(
        (fastcharger.EV_traffic < fastcharger.installed*fastcharger.carsperhour), 
        fastcharger.installed*fastcharger.carsperhour)

    # determine the power demand from EVs charging
    power = -fastcharger.EV_to_chargers * fastcharger.EV_charge_amount / fastcharger.efficiency

    return power

def FinanicalFunction(PV, wind, battery, charger, consumption, grid):
    
    class Finance:
        pass
    
    finance = Finance()
    
    # ----
    # capex breakdown
    wind.capex = wind.installed * wind.cost 
    PV.capex = PV.installed * PV.cost 
    battery.capex = battery.installed * battery.cost 
    charger.capex = charger.installed * charger.cost 
    
    # capex sum
    finance.capex = wind.capex \
            + PV.capex \
            + battery.capex \
            + charger.capex
    
    # ----        
    # opex breakdown
    wind.opex = wind.om * wind.installed
    PV.opex = PV.om * PV.installed
    battery.opex = battery.om * battery.installed
    
    # opex sum
    finance.opex =  wind.opex \
            + PV.opex \
            + battery.opex 
    
    
    # ----
    # income by part
    charger.income = -charger.yearly * charger.price * charger.efficiency
    consumption.income = -consumption.yearly * consumption.price
    grid.income = - grid.load.yearly * grid.price - grid.power.yearly * grid.cost
    
    # income balance
    finance.income = charger.income \
            + consumption.income \
            + grid.income
            
    finance.net_income = finance.income - finance.opex
    finance.IRR = finance.net_income / finance.capex  
    finance.PBY = finance.capex / finance.net_income
    
    
    return finance

def BatteryControlf(balance, battery, start_future = '1/1/2021'):
    # This function is messy and should be updated!                                 UPDATE ME!
    # currently it behaves from the perspective of the battery and is later 
    # converted to its inverse for correct power/load behaviour.
    
    # Initiate empty lists and starting SOC
    soc = []
    batcharge = []
    batstat = battery.startingSOC * battery.installed

    for index, value in balance.one.iteritems():
        bal = value

        # charging
        if batstat < battery.installed and bal > 0:
            charge_room = battery.installed - batstat
            if bal >= battery.dischargepower : # over-kill power
                charge = min(battery.dischargepower, charge_room)
            elif bal < battery.dischargepower: # fillable power
                charge = min(bal, charge_room)
            batstat += charge
            
        # discharging
        elif batstat > 0 and bal < 0:
            discharge_room = -batstat
            if bal <= -battery.dischargepower : # over-kill power
                charge = max(-battery.dischargepower, discharge_room)
            elif bal > -battery.dischargepower: # fillable power
                charge = max(bal, discharge_room)
            batstat += charge

        # perfect balance
        else:
            charge = 0
            
        soc.append(batstat)
        batcharge.append(charge)
    
    # ---------- 
    # Store to Data Frames and set times
       
    # SOC
    batterypower = pd.Series(batcharge)
    batterypower.index = pd.date_range(start_future, periods=8760, freq="1h")
    # convert to correct load/power
    battery.load = - batterypower.where(batterypower >=0, 0)
    battery.power = - batterypower.where(batterypower <=0, 0)
    battery.weekly = (battery.power + battery.load).groupby(_Weeks()).sum()
    
    # determine storage values
    battery.storage = pd.Series(soc)
    battery.storage.index = pd.date_range(start_future, periods=8760, freq="1h")
    battery.storage.weekly = battery.storage.groupby(_Weeks()).mean()
    
    # and add the SOC as attribute
    battery.storage.SOC = battery.storage / battery.installed
    battery.storage.SOC.weekly = battery.storage.SOC.groupby(_Weeks()).mean() 
    
    return battery


def _Weeks():
    indices = np.arange(0,8760)                   # actually 52.17
    _Weeks = pd.DataFrame(index = indices).index // 168
    _Weeks = np.where((_Weeks== 52),51,_Weeks)
    return _Weeks


def id_extractor_external(etmDemand_instance, scenario_id):
        etmd = etmDemand_instance
        # if 4 digit and not None (also len = 4) then extract id
        if len(str(scenario_id)) == 4 and scenario_id is not None:

            url = f"https://pro.energytransitionmodel.com/saved_scenarios/{scenario_id}/load"
            r = requests.get(url)
            if r.status_code != 200:
                raise ValueError("Response not 200!")

            soup = BeautifulSoup(r.content, "html.parser")

            scripts = soup.find_all("script")
            for script in scripts:
                string = script.string
                if string is not None and string.find("preset_scenario_id") > 0:
                    start = (
                        string.find("preset_scenario_id")
                        + len("preset_scenario_id")
                        + 2
                    )
                    end = start + 6
                    preset_scenario_id = int(string[start:end])

            _scenario_id = preset_scenario_id
            etmd.locked = True  # due to using preset_scenario_id
            etmd.title = soup.find("span", attrs={"class": "name"}).text[1:-1]

        # if 6 digit or None then just keep that id
        elif len(str(scenario_id)) == 6 or scenario_id is None:
            _scenario_id = scenario_id
            etmd.locked = False
            etmd.title = etmd.get_title(_scenario_id)

        else:
            raise ValueError(f"Scenario ID provided is not valid: {scenario_id}")

        return _scenario_id