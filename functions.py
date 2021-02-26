import pandas as pd
import numpy as np


def Consumptionf(start_future, consumption, wind_dataset_location):
    temp_consumption = pd.read_csv(wind_dataset_location,
                         nrows=35040,skiprows=5,usecols=[3])
    temp_consumption.columns = ["Consumption"]
    # Sum the data from every 15 mins to 1 hour
    temp_consumption = temp_consumption["Consumption"].groupby(temp_consumption.index // 4).sum()
    # Set the dates 
    temp_consumption.index = pd.date_range(start_future, periods=8760, freq="1h")
    # Scale the consumption to appropriate size
    consumption.load= -temp_consumption*consumption.scaler
    consumption.yearly = consumption.load.sum()
    consumption.weekly = consumption.load.groupby(_Weeks()).sum()
    return consumption



def Balancef(wind, PV, consumption, charger):
    class balance:
        pass
    balance.power = PV.power + wind.power - consumption.load - charger.load
    balance.weekly = PV.weekly + wind.weekly - consumption.weekly - charger.weekly
    # Calculate yearly balance
    balance.yearly = wind.yearly + PV.yearly - consumption.yearly - charger.yearly
    return balance

def BatteryControlf(start_future, balance, battery):
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
    
    # determine sink (storage) values
    battery.sink = pd.Series(soc)
    battery.sink.index = pd.date_range(start_future, periods=8760, freq="1h")
    battery.sink.weekly = battery.sink.groupby(_Weeks()).mean()
    
    # and add the SOC as attribute
    battery.sink.SOC = battery.sink / battery.installed
    battery.sink.SOC.weekly = battery.sink.SOC.groupby(_Weeks()).mean() 
    
    return battery

def Chargerf(charger, EV, filepath):
    EV.traffic = pd.read_pickle(filepath)
    EV.charge = EV.traffic.where((EV.traffic < charger.installed*charger.carsperhour), charger.installed*charger.carsperhour)
    EV.charge.yearly = EV.charge.sum()
    EV.traffic.yearly = EV.traffic.sum()
    charger.load = -EV.charge * EV.battery / charger.efficiency
    charger.weekly = charger.load.groupby(_Weeks()).sum()
    charger.yearly = charger.load.sum()
    return charger, EV

def FinanicalFunction(PV, wind, battery, charger, consumption, grid):
    
    class finance:
        pass
    
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

def _Weeks():
    indices = np.arange(0,8760)                   # actually 52.17
    _Weeks = pd.DataFrame(index = indices).index // 168
    _Weeks = np.where((_Weeks== 52),51,_Weeks)
    return _Weeks



