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

class ControllableBattery:
    #TODO
    # die ControllableBattery muss ohne controller erzeugt werden (weil zum
    # Zeitpunkt der Erzeugung noch gar kein Controller existiert - und wenn
    # der Kontroller dann erzeugt wird, dann brauch er die Batterien alle)
    # => methode add_controller, die aufgerufen wird, sobald der controller
    # existiert
    def __init__(self,net, at_load, according_bus, energy, power,
                 distance_travelled, consumption, arrival, u_ls=4.2, u_n=3.6,
                 i_ls=0.3, s=80):
        self.at_load = at_load
        self.according_bus = according_bus
        self.energy = energy
        self.power = power
        self.according_bus = according_bus
        self.current_power = self.energy - consumption*distance_travelled/100
        self.current_power = 0
        self.arrival_time = arrival
        self.controller = None
        
        
    def register_controller(self, controller):
        self.controller = controller
        
        
    def calc_soc(self, timestep):
        pass
        #if timestep < self.
        
    
    def calc_power(self, timestep):
        if timestep < self.arrival_time:
            self.current_power = 0
            
        else:
            if self.soc < 80:
                self.current_power = self.power
                
            else:
                # die komische Formel P(SOC)
                pass
    
    
    def _write_to_controller_ds(self, timestep):
        self.calc_soc(timestep)
        self.calc_power(timestep)
        self.controller.data_source.df.at[timestep, self.according_bus] = \
            self.current_power
    
    
    def slow_down(self, du):
        pass
        #TODO
        # der controller muss sagen, um wieviel das Spannungsband verletzt
        # worden ist, dann entsprechend diejenige Leistung, welche normal jetzt
        # anliegen würde, um einen bestimmten Wert dP(dU) absenken