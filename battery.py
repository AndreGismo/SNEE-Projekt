# -*- coding: utf-8 -*-
"""
Created on Wed May 19 17:28:30 2021

@author: andre
Klasse für den Akku vom E-Auto. Aus Werten wie Kapazität, Ladeleistung, Lade-
schlussspannung und -strom etc. wird ein Ladeprofil erzeugt. Dieses Ladeprofil
wird dann dem E-Auto übergeben.
Das fertige Lastprofil muss bereits vor dem Aufruf von
pp.timeseries.run_timeseries vorliegen
 
------------------------------------------------------------------------------
EDIT: es wird eigentlich nur die aktuelle Ladeleistung beim aktuellen soc
      berechnet, anstatt die komplette Kurve zu speichern
------------------------------------------------------------------------------
EDIT: dann mal run_battery (immer nur ein timestep: also erst
      calc_load_curve, dann calc_soc) programmieren und ausprobieren
------------------------------------------------------------------------------
EDIT: eigentlich interessiert es ja nicht, wann der Verbrauch zustande
      gekommen ist, sondern nur, wie viel bis zum Beginn vom Ladevorgang
      verbraucht worden ist => alle Werte auf 0 setzen und erst bei load_start
      beginnen mit capacity-used_energy
"""
import numpy as np
import pandas as pd
import pptools as ppt


class Battery:
    '''
    Objekte repräsentieren den Akku eines E-Fahrzeugs.
    '''
    def __init__(self, energy_used, p_load_max, load_switch, capacity, u_norm,
                 u_ls, i_ls, load_start):
        '''
        Objekte repräsentieren den Akku eines E-Fahrzeugs. "energy_used" gibt
        die seit dem letzten Ladevorgang verbrauchte Energie an. "p_load_max"
        gibt die maximale Ladeleistung an. "load_switch" gibt an, ab welchem
        Teil der Akkuladung die Ladeleistung einbricht. "capacity" gibt die
        Kapazität des Akkus an. "u_norm" ist die Nennspannung, "u_ls" die
        Ladeschluss-Spannung, "i_ls" der Ladeschluss-Strom und "load_start"
        ist die Uhrzeit, wann der Ladevorgang beginnen soll.

        Parameters
        ----------
        energy_used : float
            seit dem letzten Ladevorgang verbrauchte Energie [kWh]
        p_load_max : float
            maximale Ladeleistung [kW]
        load_switch : float
            Ladestand, ab dem die Ladeleistung abfällt [100%]
        capacity : float
            Kapazität des Akkus [kWh]
        u_norm : float
            Nennspannung des Akkus [V]
        u_ls : float
            Ladeschluss-Spannung des Akkus [V]
        i_ls : float
            Ladeschluss-Strom des Akkus [A]
        load_start : int
            Uhrzeit [hh], wann der Ladevorgang beginnt

        Returns
        -------
        None.

        '''
        self.energy_used = energy_used
        self.p_load_max = p_load_max
        self.load_switch = load_switch
        self.capacity = capacity
        self.soc = self.capacity-self.energy_used
        self.u_norm = u_norm
        self.u_ls = u_ls
        self.i_ls = i_ls
        self.p_load = None
        self.calc_p_load()
        self.load_start = load_start
        self.is_logging = False
        self.timeseries = pd.DataFrame([[0, 0] for i in range(96)],
                                       columns=['soc [kWh]', 'p_load [kW]'])
        
    def calc_p_load(self):
        p_ls = self.u_ls/self.u_norm*self.i_ls*self.capacity
        i_ls = (1-self.load_switch)/np.log(self.p_load_max/p_ls)
        self.p_load = self.p_load_max-np.exp((self.load_switch-self.soc/self.capacity)/i_ls)
        
    def calc_soc(self):
        self.soc += self.p_load/4
        
    def run_battery(self):
        i = 0
        while self.soc <= self.capacity-4:
            if self.is_logging:
                self.timeseries.loc[i, 'soc [kWh]'] = self.soc
                self.timeseries.loc[i, 'p_load [kW]'] = self.p_load
            self.calc_p_load()
            self.calc_soc()
            i += 1
        self.timeseries = ppt.shift_profile(self.timeseries, self.load_start*8)
            
    def start_log(self):
        self.is_logging = True