# -*- coding: utf-8 -*-
"""
Created on Wed May 19 17:28:30 2021

@author: andre
Klasse für den Akku vom E-Auto. Aus Werten wie Kapazität, Ladeleistung, Lade-
schlussspannung und -strom etc. wird ein Kennlinie von P(SOC) erstellt. Dann
kann zu jedem Zeitpunkt in Abhängigkeit des SOC die aktuelle Ladeleistung P
abgelesen werden.
"""
import numpy as np
import pandas as pd
import pptools as ppt


class Battery:
    '''
    Objekte repräsentieren den Akku eines E-Fahrzeugs.
    '''
    def __init__(self, e_bat, p_const, u_ls=4.2, u_n=3.6, i_ls=0.03, s=80):
        self.e_bat = e_bat
        self.p_const = p_const
        self.u_ls = u_ls
        self.u_n = u_n
        self.i_ls = i_ls
        self.s = s
        self.load_curve = self.calc_load_curve()
        
    def calc_load_curve(self):
        soc = np.linspace(0, 100, 101)
        p_ls = self.u_ls/self.u_n * self.i_ls * self.e_bat
        k_l = (100-self.s)/(np.log(self.p_const/p_ls))
        p = self.p_const*np.exp((self.s-soc)/k_l)    
        # bis zu s % Ladestand ist P = P_konst
        p[:self.s] = self.p_const
        # für 100% Ladestand ist P = 0
        p[-1] = 0
        return p
    
    def calc_load_profile(self, load_kwh):
        length = 96
        time = np.linspace(0, length-1, length)
        load = []
        power = []
        load_percent = load_kwh/self.e_bat
        
        for sec in time:
            if load_percent < 101:
                load_percent = int(np.round(load_kwh/self.e_bat*100, 0))
                # damit der Ladestand nicht größer 100 wird
                if load_percent > 100:
                    load_percent = 100
                load_kwh += self.load_curve[load_percent]/4
                load.append(load_kwh)
                power.append(self.load_curve[load_percent])
            
        load = np.array(load)
        power = np.array(power)
        
        return power
        
        
        
        
        