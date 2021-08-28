# -*- coding: utf-8 -*-
"""
Created on Sat Jun 19 10:05:34 2021

@author: andre
ein smarter Controller für die Batterien (also für denjenigen Teil vom Last-
profil, der von der battery kommt). Für jeden timestep soll geprüft werden, ob
die Spannung an demjenigen Knoten, an dem sich die entsprechende Batterie be-
findet bereits um mehr als 6% gefallen ist. Wenn ja, dann soll die bezogene
Leistung gemäß einer P(U)-Kennlinie verringert werden.
Als data_source wird also ein df übergeben, welches nur die Ladekurven aller
E-Autos beinhaltet.
Brauch noch so eine Art "battery_pool", wo alle Batterien drin sind, dass er
sich bei jedem timestep durchiterieren kann und gegebenfalls bestimmte Baterien
drosselt
"""

import pandapower as pp
from pandapower import control
import pandas as pd
from pandapower import timeseries as ts


class BatteryController(control.controller.const_control.ConstControl):
    
    # self.need_action erstmal weggelassen. Für jede Batterie (also an dem
    # zugehörigen Knoten) wird zu jedem timestep geprüft, wie weit die Spannung
    # gefallen ist. Diese Differenz wird beim Aufruf von bat.write_to_controller_ds
    # übergeben, damit die jeweilige Batterie entsprechend ihre Leistung reduzieren
    # kann. PROBLEM: den Zustand vom Netz kennt man nur nach der Netzberechung
    # im aktuellen timestep (wofür man wiederum alle Lasten benötigt - welche
    # man ja wiederum in Abhängigkeit des Netzzustandes berechnen möchte)
    # => den Zustand vom Netz im letzten timestep nehmen
    # order und level jeweils 0
    # check violations erst nach super.timestep(net)? weil erst dann die Ergebnisse
    # im net stehen

    voltage_violations = 0
    violated_buses = set()
    
    def __init__(self, net, element, variable, element_index, batteries, data_source=None, second_ds=None,
                 in_service=True, recycle=False, order=0, level=0, **kwargs):
        super().__init__(net, in_service=in_service, recycle=recycle, data_source=data_source,
                         element_index=element_index, order=order, level=level,
                         element=element, variable=variable,
                         initial_powerflow = True, **kwargs)
        self.profile_name = self.element_index
        self.need_action = False
        self.batteries = batteries
        self.net_status = pd.DataFrame(index=net.load.index,
                                       columns=['corresponding bus nr.',
                                                'battery available',
                                                'delta voltage'])
        self.prepare_net_status(net)
        self.register_for_batteries()
        self.activate_controlling = False
        self.second_ds = second_ds
        
    
    def activate_contolling(self):
        self.activate_controlling = True
        for bat in self.batteries:
            bat.activate_controlling = True
    
    
    def prepare_net_status(self, net):
        self.net_status.loc[:, 'corresponding bus nr.'] = net.load.bus
        self.net_status.loc[:, 'battery available'] = 0
        self.net_status.loc[:, 'delta voltage'] = 0
        for bat in self.batteries:
            self.net_status.at[bat.at_load, 'battery available'] = 1
        
    
    def time_step(self, net, time):
        # schauen, ob es Verletzungen vom Spannungsband gab
        #self.check_violations(net, time)
        # falls nicht, die batteries ganz normal die datasource beschreiben lassen
        #if not self.need_action:
        for bat in self.batteries:
            delta_u = self.net_status.at[bat.at_load, 'delta voltage']
            bat._write_to_controller_ds(time, delta_u)
        
        # falls doch
        #else:
            #for bat in self.batteries:
                #if bat.according_bus in type(self).violated_buses:
                    #bat.print_violated(time)
                    #TODO
                    # entsprechend reagieren => Leistung der bat runter
                    #self.need_action = False
                    #type(self).violated_buses = set()
                    #pass
        
        # die normale time_step ausführen
        #super().time_step(net, time)
        self.values = self.data_source.get_time_step_value(time, self.profile_name)
        self.write_with_loc(net, time)
        self.check_violations(net, time)
    
    
    def write_with_loc(self, net, time):
        # erstmal die Werte zu dem timestep aus der Datasource vom ConstController
        # der Ps holen (dann barucht man diesen Controller auch nicht mehr)
        # => dann die Werte an dieselbe Stelle schreiben, wo gleich darauf die
        # Werte aus der eigenen DataSource reinkommen
        sds_values = self.second_ds.get_time_step_value(time, net.load.index)
        self.values += sds_values
        #net[self.element].loc[net.load.index, self.variable] = sds_values
        net[self.element].loc[self.element_index, self.variable] += self.values
        print('\nmeine eigenen write_with_loc führt gerade aus!!')
        if time == 95:
            print('\nDatentyp von values:', self.values)
            print('\nDatentype von sds_values:', sds_values)
        
        
    def check_violations(self, net, time):
        for num, voltage in enumerate(net.res_bus['vm_pu']):
            if voltage < 0.94:
                type(self).voltage_violations += 1
                type(self).violated_buses.add(num)
            
            #print('Spannung: ', voltage)
            delta_u = 1 - voltage
            #print('\ndelta u: ', delta_u)
            self.net_status.at[num, 'delta voltage'] = delta_u
            #if type(self).voltage_violations >= 1:
                #self.need_action = True
                #print('\nhallo, ich wurde ausgeführt :)')
        
    
    #TODO
    # das sollte wohl eher in der ControllableBattery geschehen
    # das zurücksetzen vom Alarm muss dann noch hier irgendwo geschehen
    def react(self, time):
        for bat in self.batteries:
            if bat.according_bus in type(self).violated_buses:
                bat.slow_down()
                
            # erstmal wieder Alarm zurück, da ja reagiert worden ist
            self.need_action = False
            type(self).violated_buses = set()
    
        
    def get_voltage_violations(self):
        return type(self).voltage_violations
    
    
    def get_violated_buses(self):
        return type(self).violated_buses
    
    
    def register_for_batteries(self):
        for bat in self.batteries:
            bat.register_datasource(self.data_source)
        
        
        