# -*- coding: utf-8 -*-
"""
Created on Sat Jun 12 06:46:18 2021

@author: andre

Klasse Scenario, in der man festlegen kann, wie viele e-Fahrzeuge es
gibt (penetration), usw....
"""

import pandas as pd
import numpy as np


class Scenario:
    
    __DISTANCES = {'distance travelled [km]':[20, 30, 40, 50, 60],
                   'probability':[0.13, 0.29, 0.30, 0.15, 0.13]}
    __DISTANCES = pd.DataFrame(__DISTANCES)
    __DISTANCES.set_index('distance travelled [km]', inplace=True)
    
    __LOAD_POWERS = {'power [kW]':[3.7, 11.1, 22.2],
                     'probability':[0.35, 0.55, 0.10]}
    __LOAD_POWERS = pd.DataFrame(__LOAD_POWERS)
    __LOAD_POWERS.set_index('power [kW]', inplace=True)
    
    __ARRIVALS = pd.read_csv('Daten/Statistiken/arrivals96.csv', sep=';')
    __ARRIVALS.drop('time', axis=1, inplace=True)
    __ARRIVALS.index = range(len(__ARRIVALS))
    
    __CONSUMPTIONS = {'consumption [kWh/100km]':[13, 15, 17, 19, 21, 23],
                      'probability':[0.3, 0.2, 0.15, 0.15, 0.1, 0.1]}
    __CONSUMPTIONS = pd.DataFrame(__CONSUMPTIONS)
    __CONSUMPTIONS.set_index('consumption [kWh/100km]', inplace=True)
    
    __BATTERY_SIZES = {'battery size [kWh]':[20, 30, 40, 50, 60, 70, 80],
                       'probability':[0.09, 0.12, 0.18, 0.20, 0.25, 0.08, 0.08]}
    __BATTERY_SIZES = pd.DataFrame(__BATTERY_SIZES)
    __BATTERY_SIZES.set_index('battery size [kWh]', inplace=True)
    
    STATISTICS = {'distances':__DISTANCES,
                  'load powers':__LOAD_POWERS,
                  'arrivals':__ARRIVALS,
                  'consumptions':__CONSUMPTIONS,
                  'battery sizes':__BATTERY_SIZES}
    
    def __init__(self, net, penetration):
        self.net_buses = net.bus
        self.net_loads = net.load
        self.num_loads = len(net.load.index)
        self.penetration = penetration
        self.num_chargers = int(np.round(self.num_loads * penetration/100, 0))
        self.loads_available = list(net.load.index)
        
        self.scenario_data = pd.DataFrame(index=range(self.num_chargers),
             columns=['load nr.', 'according bus nr.', 'charging power [kW]', 'time of arrival',
                      'distance travelled [km]', 'consumption [kWh/100km]',
                      'battery size [kWh]'])
        
        #self.get_corresponding_buses()
        self.get_scenario_data()
        
        
    def get_corresponding_bus(self):
        choice = np.random.choice(self.loads_available)
        choosen_load = self.loads_available.pop(self.loads_available.index(choice))
        according_bus = self.net_buses.index[self.net_loads.at[choosen_load,
                                                               'bus']]
        return choice, according_bus
        
        
    def get_scenario_data(self):
        for i in self.scenario_data.index:
            choosen_load, according_bus = self.get_corresponding_bus()
            self.scenario_data.at[i, 'according bus nr.'] = according_bus
            self.scenario_data.at[i, 'load nr.'] = choosen_load
            
            self.scenario_data.at[i, 'charging power [kW]'] = np.random.choice(
                type(self).__LOAD_POWERS.index,
                p=type(self).__LOAD_POWERS['probability'])
                
            self.scenario_data.at[i, 'time of arrival'] = np.random.choice(
                type(self).__ARRIVALS.index,
                p=type(self).__ARRIVALS['probability'])
            
            self.scenario_data.at[i, 'distance travelled [km]'] = np.random.choice(
                type(self).__DISTANCES.index,
                p=type(self).__DISTANCES['probability'])
            
            self.scenario_data.at[i, 'consumption [kWh/100km]'] = np.random.choice(
                type(self).__CONSUMPTIONS.index,
                p=type(self).__CONSUMPTIONS['probability'])
            
            self.scenario_data.at[i, 'battery size [kWh]'] = np.random.choice(
                type(self).__BATTERY_SIZES.index,
                p=type(self).__BATTERY_SIZES['probability'])
            
            for col in self.scenario_data.columns:
                if not col == 'time of arrival':
                    self.scenario_data.loc[:, col] = pd.to_numeric(
                        self.scenario_data[col])
            
            
            
            
        
        
        
        
    
    