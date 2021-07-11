# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 08:14:04 2021

@author: andre
Klasse ControllableBattery, die während der Simulation der timeseries vom
BatteryController aufgerufen wird, um (falls nötig), die Ladeleistung einer
Batterie herunterzusetzen.
Eventuell brauchen Objekte dieser Klasse gar keine eigene timeseries, weil bei
jedem Timestep die Ojekte aufgerufen werden und dynamisch die aktuelle
Ladeleistung liefern (und der Ladestand muss natürlich auch im Hintergrund
nachgehalten werden)
"""

import numpy as np

class ControllableBattery:
    
    __data_source = None
    
    def __init__(self, net, at_load, according_bus, energy, power,
                 distance_travelled, consumption, arrival, u_ls=4.2, u_n=3.6,
                 i_ls=0.3, s=80):
        self.at_load = int(at_load)
        self.according_bus = int(according_bus)
        self.energy = energy 
        self.power = power
        self.current_energy = self.energy - consumption*distance_travelled/100
        self.current_power = 0
        self.current_soc = self.current_energy/self.energy*100
        self.arrival_time = arrival
        self.u_ls = u_ls
        self.u_n = u_n
        self.i_ls = i_ls
        self.s = s
        self.activate_controlling = False
        
        
    def register_datasource(self, datasource):
        type(self).data_source = datasource
        
        
    def calc_soc(self, timestep):
        # solange die arrival time noch nicht erreicht worden ist, geschieht
        # noch nichts
        if timestep < self.arrival_time:
            pass
        
        else:
            # für den Fall, dass ein Auto ab 00:00 beginnt zu laden
            if timestep == 0: #neu
                self.current_energy += 0 #neu
                self.current_soc = self.current_energy/self.energy*100 # neu
                
            else: #neu
                # ansonsten ist die Energie gleich der Energie des letzten
                # Zeitpunkts + der Leistung des letzten Zeitpunkts
                self.current_energy += self.data_source.df.at\
                    [timestep-1, self.at_load]/4*1000
                self.current_soc = self.current_energy/self.energy*100
        
    
    def calc_power(self, timestep):
        if timestep < self.arrival_time:
            self.current_power = 0
            
        else:
            if self.current_soc < 80:
                self.current_power = self.power
            
            #TODO
            # irgendwo hier muss der Fehler liegen, dass die Ladeleistung in
            # diesem Bereich ansteigt (eigentlich müsste die ja sinken!!)
            elif self.current_soc >= 80 and self.current_soc < 100:
                p_ls = self.u_ls/self.u_n * self.i_ls * self.energy
                k_l = (100-self.s)/(np.log(self.power/p_ls))
                self.current_power = self.power*np.exp(-(self.s-self.current_soc)/k_l)
                
            else:
                self.current_power = 0
    
    
    def _write_to_controller_ds(self, timestep, delta_u):
        #print(f'Batterie Nr. {self.at_load} sieht Spannungsdifferenz {delta_u} [%]')
        self.calc_soc(timestep)
        self.calc_power(timestep)
        if self.activate_controlling:
            self.reduce_power(timestep, delta_u)
        #self.print_interest(timestep)
        type(self).data_source.df.at[timestep, self.at_load] = self.current_power/1000
    
    
    def reduce_power(self, timestep, delta_u):
        # reduziert die Ladeleistung in Abhängigkeit der
        # Spannungsunterschreitung
            
        if delta_u < 0.005:
            factor = 1
            
        elif delta_u >= 0.005 and delta_u < 0.01: # schwächste Steigung
            factor = -2.5 * delta_u + 1.1
            
        elif delta_u >= 0.01 and delta_u < 0.03: # schwache Steigung
            factor = -5 * delta_u + 1.1
            
        elif delta_u >= 0.03 and delta_u < 0.06: # normale Steigung
            factor = -0.5/0.05 * delta_u + 1.1
            
        elif delta_u >= 0.06: #
            factor = 0.5
            
        #print('\nerrechneter Faktor für Batterie Nr. {} zum Zeitpunkt {}: {} aufgrund delta_u {}'.format(self.at_load, timestep, factor, delta_u))
        self.current_power *= factor
            
        
    def print_interest(self, timestep):
        if self.at_load == 17:
            print(f'\nLadestand zum timestep {timestep}: {self.current_soc}')
            print(f'Ladeleistung zum timestep {timestep}: {self.current_power}\n')
            
            
    def print_violated(self, timestep):
        print('Batterie am Knoten {} (Last Nr {}) reagiert zu Zeitschritt {}.\
              '.format(self.according_bus, self.at_load, timestep))