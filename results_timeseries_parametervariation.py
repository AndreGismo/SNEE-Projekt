# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 06:24:04 2021

@author: andre
wie kerber_timeseries, aber mal in einer Schleife unterschiedliche Regel-
parameter einstellen
"""
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import os
import seaborn as sns
import pandapower.networks as pn
import pandapower as pp
import pandapower.control as control
import pandapower.timeseries as timeseries
from pandapower.timeseries.data_sources.frame_data import DFData
import pandapower.plotting as pt
import plotly.graph_objs as go
import plotly.io as pio
# damit man sich nach dem manuellen hinzufügen einer weiteren trace den plot
# nochmal anzeigen lassen kann im browser
pio.renderers.default = 'browser'

import pptools as ppt
from battery import Battery
from scenario import Scenario
from battery_controller import BatteryController
from controllable_battery import ControllableBattery

till = 21

kis = [i/10 for i in range(0, till)]
kds = [i/10 for i in range(0, till)]

results = pd.DataFrame(index=range(till**2), columns=['Anzahl', 'Ki', 'Kd'])
counter = 0
for ki in kis:
    ControllableBattery.set_control_params('Ki', ki)
    for kd in kds:
        ControllableBattery.set_control_params('Kd', kd)
        # Variablen zum Steuern der simulierten Szenarien
        same_arrival = True
        arrival_time = 46
        
        same_power = True
        loading_power = 11.1
        
        same_travelled = True
        distance_travelled = 200
        
        controlling = True
        
        cosphi = 0.9
        
        
        #### Netz bauen ##############################################################
        # leeres Netz erzeugen
        net = pn.create_kerber_vorstadtnetz_kabel_1()
        
        #### Szenario erzeugen #######################################################
        fun_scenario = Scenario.load_scenario('Szenario100')
        
        if same_arrival:
            fun_scenario.set_constant('time of arrival', arrival_time, inplace=True)
            
        if same_power:
            fun_scenario.set_constant('charging power [kW]', loading_power,
                                      inplace=True)
            
        if same_travelled:
            fun_scenario.set_constant('distance travelled [km]', distance_travelled,
                                      inplace=True)
            
        #fun_scenario.distribute_loads(inplace=True, near_trafo=True)
            
        #### Daten für die einzelnen loads erzeugen (96, 146) ########################
        # das sind die Daten vom 13.12.2020, weil es da den höchsten peak gab
        data_nuernberg = pd.read_csv('Daten/Lastprofil/Nuernberg_absolut_final.csv')
        
        baseload = ppt.prepare_baseload(data_nuernberg, net)
        
        batteries, datasource_bat = ppt.prepare_batteries(net, fun_scenario)
        
        #### data source erzeugen ####################################################
        loads = DFData(baseload)
        
        # Faktor für Anteil Q an P aus cosphi errechnen
        faktor = (1/cosphi**2 -1)**0.5
        
        # data_source für Q
        loads_q = DFData(baseload * faktor)
        
        # data_source für Ladekurven der e-Autos
        loads_bat = DFData(datasource_bat)
        
        # controler erzeugen, der die Werte der loads zu den jeweiligen Zeitpukten
        # entsprechend loads setzt
        load_controler = control.ConstControl(net, element='load', variable='p_mw',
                                              element_index=net.load.index,
                                              data_source=loads,
                                              profile_name=net.load.index)
        
        load_controler_q = control.ConstControl(net, element='load', variable='q_mvar',
                                              element_index=net.load.index,
                                              data_source=loads_q,
                                              profile_name=net.load.index)
        
        load_controller_bat = BatteryController(net, element='load', variable='p_mw',
                                                element_index=datasource_bat.columns,#loading_data.columns,
                                                data_source=loads_bat, batteries=batteries)
        
        if controlling:
            load_controller_bat.activate_contolling()
        
        
        # output writer erzeugen, der die Ergebnisse für jeden Timestep in eine
        # csv-Datei je load schreibt
        writer = timeseries.OutputWriter(net, output_path="./",
                                         output_file_type=".csv")
        
        # festlegen, welche Variablen geloggt werden sollen
        writer.log_variable(table='res_bus', variable='vm_pu')
        writer.log_variable(table='res_line', variable='loading_percent')
        writer.log_variable(table='res_trafo', variable='loading_percent')
        
        # timeseries simulieren ((95+1) * 15min = 1Tag)
        timeseries.run_timeseries(net, verbose=False)
        print('\n--------------------------------------------------------------------')
        print('Anzahl der Spannungsbandverletzungen: {}'.format(load_controller_bat.voltage_violations))
        print('Durchlauf {} von {}'.format(counter, till**2))
        print('\n--------------------------------------------------------------------')
        
        results.loc[counter, :] = [load_controller_bat.voltage_violations, ki, kd]
        counter += 1
        
#results.to_csv('Ergebnisse_Reglung.csv', index=False)
        
results['Ki'] *= 10
results['Kd'] *= 10

results['Ki'] = results['Ki'].astype(int)
results['Kd'] = results['Kd'].astype(int)

results['Anzahl'] = results['Anzahl'].diff()
#results.drop(0, axis=0, inplace=True)
results.to_csv('Ergebnisse_Reglung.csv', index=False)

res_piv = results.pivot(index='Ki', columns='Kd', values='Anzahl')
sns.heatmap(res_piv)
