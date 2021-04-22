# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 14:16:40 2021

@author: Sethv
"""

import numpy as np
import pandas as pd


def merit_order(components, merit_order_dict, start_date):
    """
    
        Based on supplied component list this function checks the merit_tag and
        and interprets this based on the merit_order dictionary. 
        
        
        
        
    """
    # optionally; include a 'state' input variable to make balances for dif-
    # ferent types of energies.
    state = 'power'
    
    balance = pd.DataFrame(
                index = pd.date_range(
                start_date, 
                periods=8760, 
                freq="1h"))
    
    cmlvl = 1
    
    while cmlvl <= max(merit_order_dict.values()):
        
        balance[cmlvl] = balance[cmlvl-1] if cmlvl > 1 else 0
        
        for component in components:
        
            if merit_order_dict[component.merit_tag] == cmlvl:
                
                print('Current LVL: {}'.format(cmlvl) + 
                      '  --> {}'.format(component.__str__())
                      )
                
                if hasattr(component, 'power_control'):
                    
                    print('{} has power_control'.format(component.__str__()))
                    
                    component.power_control(balance[cmlvl])
                    balance[cmlvl] += component.state[state]
                
                else:   
                    
                    print('{} added '.format(component.__str__()) + 
                          f'to balance {cmlvl}: '
                          + '{}'.format(component.state.power.sum()))
                    
                    balance[cmlvl] += component.state[state]
           
        cmlvl += 1
            
            
        
        

    
    
    
    return balance


def battery_power_control(battery_instance, balance_in):
    
    battery = battery_instance
    
    _energy = []
    _power = []
    
    
    ienergy = battery.startingSOC * battery.installed

    for index, balance in balance_in.iteritems():
        
        # ----- intra-battery power perspective ----- #
        # =========================================== #
        
        # charging --> positive ipower value
        if ienergy < battery.installed and balance > 0: 
            # |--> battery not full
            # |--> positive balance
            
            max_charge = battery.installed - ienergy 
            
            if balance >= battery.dischargepower : # over-kill power
                ipower = min(battery.dischargepower, max_charge)
            elif balance < battery.dischargepower: # fillable power
                ipower = min(balance, max_charge)

            ienergy += ipower
            # |--> ipower is positive
            # |--> add hourly power to energy for next hour
            
            
        # discharging --> source --> positive power on energy balance
        elif ienergy > 0 and balance < 0:
            # |--> battery not empty
            # |--> negative balance
            
            
            max_discharge = -ienergy
            if balance <= -battery.dischargepower : # over-kill power
                ipower = max(-battery.dischargepower, max_discharge)
            elif balance > -battery.dischargepower: # fillable power
                ipower = max(balance, max_discharge)
            
            ienergy += ipower

        # perfect balance
        else:
            ipower = 0

        # ----- general source/sink power convention ----- #
        # ================================================ #
        
        _energy.append(ienergy)
        _power.append(-ipower)
        # |--> invert sign because charge is sink, discharge is source
            

    # power state
    power = pd.Series(_power)
    power.index = balance_in.index
    
    # energy state
    energy = pd.Series(_energy)
    energy.index = balance_in.index
    
    return power, energy

def grid_power_control(grid_instance, balance_in):
    
    grid = grid_instance
    
    # where balance is negative, we will import
    power_in = -balance_in.where( balance_in<0 , 0.0)
    
    # where import is greater than grid capacity, we cap to grid capacity
    power_in = power_in.mask( power_in > grid.installed , grid.installed)
    
    # EXPORT
    # where balance is positive, we will export 
    power_out = -balance_in.where( balance_in > 0, 0.0)
    # where export is greater than grid capacity, we cap to grid capacity
    power_out = power_out.mask( power_out < -grid.installed, -grid.installed)
    
    # combine import and export
    power = power_in + power_out
    
    
    return power