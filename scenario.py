# -*- coding: utf-8 -*-
"""
Created on Sat Jun 12 06:46:18 2021

@author: andre

Klasse Scenario, in der man festlegen kann, wie viele e-Fahrzeuge es
gibt (penetration), usw....
"""

import pandas as pd
import numpy as np
import pickle
import copy


class Scenario:
    
    __DISTANCES = {'distance travelled [km]':[7, 21, 35, 50, 60],
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
    
    # Mittelwert nehmen?
    __CONSUMPTIONS = {'consumption [kWh/100km]':[17.7],#[13, 15, 17, 19, 21, 23],
                      'probability':[1]}#[0.3, 0.2, 0.15, 0.15, 0.1, 0.1]}
    __CONSUMPTIONS = pd.DataFrame(__CONSUMPTIONS)
    __CONSUMPTIONS.set_index('consumption [kWh/100km]', inplace=True)
    
    # Mittelwert nehmen?
    __BATTERY_SIZES = {'battery size [kWh]':[52],#[20, 30, 40, 50, 60, 70, 80],
                       'probability':[1]}#[0.09, 0.12, 0.18, 0.20, 0.25, 0.08, 0.08]}
    __BATTERY_SIZES = pd.DataFrame(__BATTERY_SIZES)
    __BATTERY_SIZES.set_index('battery size [kWh]', inplace=True)
    
    __SECOND_CAR = {'number of ecars':[1, 2],
                    'probability':[0.8, 0.2]}
    __SECOND_CAR = pd.DataFrame(__SECOND_CAR)
    
    STATISTICS = {'distances':__DISTANCES,
                  'load powers':__LOAD_POWERS,
                  'arrivals':__ARRIVALS,
                  'consumptions':__CONSUMPTIONS,
                  'battery sizes':__BATTERY_SIZES,
                  'number ecars':__SECOND_CAR}

    
    def __init__(self, net, penetration):
        self.net_buses = net.bus
        self.net_loads = net.load
        self.num_loads = len(net.load.index)
        self.penetration = penetration
        self.num_chargers = int(np.round(self.num_loads * penetration/100, 0))
        self.loads_available = list(net.load.index)
        self.resolution = None
        self.factor = None
        
        self.scenario_data = pd.DataFrame(index=range(self.num_chargers),
             columns=['load nr.', 'according bus nr.', 'charging power [kW]', 'time of arrival',
                      'distance travelled [km]', 'consumption [kWh/100km]',
                      'battery size [kWh]', 'number of ecars'])
        
        #self.get_corresponding_buses()
        self.get_scenario_data()
        
        
    def set_resolution(self, resolution):
        self.resolution = resolution
        self.adapt_resolution()
        
        
    def adapt_resolution(self):
        if self.resolution == '15min':
            self.factor = 1
            pass
        
        else:
            # welcher Konversionsfaktor ergibt sich aus der neuen resolution
            self.factor = 15 / int(self.resolution.rstrip('min'))
            
            # Verteilung der Ankunftzeiten entsprechend modifizieren
            self.scenario_data.loc[:, 'time of arrival'] =\
            self.scenario_data['time of arrival'] * self.factor
        
        
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
            
            self.scenario_data.at[i, 'number of ecars'] = np.random.choice(
                type(self).__SECOND_CAR['number of ecars'],
                p=type(self).__SECOND_CAR['probability'])
            
            for col in self.scenario_data.columns:
                if not col == 'time of arrival':
                    self.scenario_data.loc[:, col] = pd.to_numeric(
                        self.scenario_data[col])
            
            #self.scenario_data['load nr.'] = self.scenario_data['load nr.'].astype(int)
                    
    
    def set_constant(self, parameter, value, at_load=None, inplace=False):
        if not inplace:
            copied = copy.deepcopy(self)
            if at_load == None:
                if parameter != 'time of arrival':
                    copied.scenario_data.loc[:, parameter] = value
                else:
                    copied.scenario_data.loc[:, parameter] = value * self.factor
            else:
                for load in at_load:
                    filt = copied.scenario_data['load nr.'] == load
                    if parameter != 'time of arrival':
                        copied.scenario_data.loc[filt, parameter] = value
                    else:
                        copied.scenario_data.loc[filt, parameter] = value * self.factor
            return copied
        
        else:
            if at_load == None:
                if parameter != 'time of arrival':
                    self.scenario_data.loc[:, parameter] = value
                else:
                    self.scenario_data.loc[:, parameter] = value * self.factor
            else:
                for load in at_load:
                    filt = self.scenario_data['load nr.'] == load
                    if parameter != 'time of arrival':
                        self.scenario_data.loc[filt, parameter] = value
                    else:
                        self.scenario_data.loc[filt, parameter] = value * self.factor
                
        
        
    @staticmethod
    def save_scenario(scenario, filename):
        path = 'Daten/Szenarien/' + filename + '.pkl'
        with open(path, 'wb') as output:
            pickle.dump(scenario, output)
            
            
    @staticmethod
    def load_scenario(filename):
        path = 'Daten/Szenarien/' + filename + '.pkl'
        with open(path, 'rb') as source:
            scenario = pickle.load(source)
        return scenario


    def distribute_loads(self, near_trafo=True, lines=None, inplace=False):
        if near_trafo:
            new_buses = []
            corresponding_loads = []
            cur_line = 1
            cur_bus = 1
            buses_to_choose = self.num_chargers
            for _ in range(39*10):
                name = 'loadbus_'  + str(cur_line) + '_' + str(cur_bus)
                for num, bus_name in enumerate(self.net_buses['name']):
                    if bus_name == name:
                        new_buses.append(num)
                        cor_load = self.net_loads.loc\
                            [self.net_loads['bus'] == num].index.values[0]
                        corresponding_loads.append(cor_load)
                        buses_to_choose -= 1
                        
                if buses_to_choose == 0:
                    break
                
                cur_line += 1
                if cur_line > 10:
                    cur_line = 1
                    cur_bus += 1
            
        if not near_trafo:
            new_buses = []
            corresponding_loads = []
            cur_line = 1
            cur_bus = 39
            buses_to_choose = self.num_chargers
            for _ in range(39*10):
                name = 'loadbus_'  + str(cur_line) + '_' + str(cur_bus)
                for num, bus_name in enumerate(self.net_buses['name']):
                    if bus_name == name:
                        new_buses.append(num)
                        cor_load = self.net_loads.loc\
                            [self.net_loads['bus'] == num].index.values[0]
                        corresponding_loads.append(cor_load)
                        buses_to_choose -= 1
                        
                if buses_to_choose == 0:
                    break
                
                cur_line += 1
                if cur_line > 10:
                    cur_line = 1
                    cur_bus -= 1
                
        
        if not inplace:
            copied = copy.deepcopy(self)
            copied.scenario_data.loc[:, 'according bus nr.'] = new_buses
            copied.scenario_data.loc[:, 'load nr.'] = corresponding_loads
            return copied
        
        else:
            self.scenario_data.loc[:, 'according bus nr.'] = new_buses
            self.scenario_data.loc[:, 'load nr.'] = corresponding_loads
        
            
            
            
        
        
        
        
    
    