# -*- coding: utf-8 -*-
"""
Created on Tue May 18 09:45:33 2021

@author: andre
Kerber-Netz simulieren über time series
"""
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import os

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


#### Szenario laden ##########################################################
scenario = pd.read_csv('Daten/Statistiken/scenario30.csv')
scenario.drop('Unnamed: 0', axis=1, inplace=True)
#### Netz bauen ##############################################################
# leeres Netz erzeugen
net = pn.create_kerber_vorstadtnetz_kabel_1()
    
#### Daten für die einzelnen loads erzeugen (96, 146) ########################
# das sind die Daten vom 13.12.2020, weil es da den höchsten peak gab
data_nuernberg = pd.read_csv('Daten/Lastprofil/Nuernberg_absolut_final.csv')
# die nervige Spalte weg
data_nuernberg.drop('Unnamed: 0', axis=1, inplace=True)
    
for i in range(len(net.load)-1):
    data_nuernberg[i+1] = data_nuernberg[data_nuernberg.columns[0]]

#choices, scenario_data = ppt.add_emobility(data_nuernberg, net, 30, True)
choices = ppt.add_emobility_like_scenario(data_nuernberg, net, scenario)
print('buses der gewählten Loads: ', choices)
#data_nuernberg.columns = net.load.index
data_nuernberg /= 1e6


#### data source erzeugen ####################################################
loads = DFData(data_nuernberg)

# controler erzeugen, der die Werte der loads zu den jeweiligen Zeitpukten
# entsprechend loads setzt
load_controler = control.ConstControl(net, element='load', variable='p_mw',
                                      element_index=net.load.index,
                                      data_source=loads,
                                      profile_name=net.load.index)

# output writer erzeugen, der die Ergebnisse für jeden Timestep in eine
# csv-Datei je load schreibt
writer = timeseries.OutputWriter(net, output_path="./",
                                 output_file_type=".csv")

# festlegen, welche Variablen geloggt werden sollen
writer.log_variable(table='res_bus', variable='vm_pu')
writer.log_variable(table='res_line', variable='loading_percent')
writer.log_variable(table='res_trafo', variable='loading_percent')

# timeseries simulieren ((95+1) * 15min = 1Tag)
timeseries.run_timeseries(net)

#### Die Ergebnisse wieder in ein DF einlesen ################################
results_bus = pd.read_csv('res_bus/vm_pu.csv', sep=';')*400
results_trafo = pd.read_csv('res_trafo/loading_percent.csv', sep=';')
results_line = pd.read_csv('res_line/loading_percent.csv', sep=';')

results_bus.index = pd.date_range(start='2020', freq='15min',
                                  periods=len(results_bus))
results_line.index = pd.date_range(start='2020', freq='15min',
                                  periods=len(results_bus))


#### herausfinden, welche Objekte am stärksten belastet sind #################
crit_bus = ppt.get_critical_bus(results_bus)
print(f'Maximal belasteter Bus: {crit_bus}')

crit_line = ppt.get_critical_line(results_line)
print(f'Maximal belastete Leitung: {crit_line}')


#### Ergebnisse graphisch darstellen #########################################
fig_bus, ax_bus = plt.subplots(1, 1, figsize=(15, 8))
ax_bus.plot(results_bus[str(crit_bus)], '-x')
ax_bus.set_title('Spannungsverlauf am meistbelasteten Knoten Nr. {}\
                 '.format(crit_bus))
ax_bus.grid()
ax_bus.set_xlabel('Zeitpunkt [MM-TT hh]')
ax_bus.set_ylabel('Spannung [V]')


fig_line, ax_line = plt.subplots(1, 1, figsize=(15, 8))
ax_line.plot(results_line[str(crit_line)], '-x')
ax_line.set_title('Verlauf der Auslastung der meistbelasteten Leitung Nr. {}\
                  '.format(crit_line))
ax_line.grid()
ax_line.set_xlabel('Zeitpunkt [MM-TT hh]')
ax_line.set_ylabel('Auslastung [%]')


samples = 10
fig_load, ax_load = plt.subplots(1, 1, figsize=(15, 8))
ax_load.plot(data_nuernberg[np.random.choice(data_nuernberg.columns, samples)]*1000,
             '-x')
ax_load.set_title('Profile von {} zufällig ausgewählte Lasten'.format(samples))
ax_load.grid()
ax_load.set_xlabel('Zeitpunkt [MM-TT hh]')
ax_load.set_ylabel('Leistung [kW]')


# Zeichnen, wie die Spannung über den einzelnen Strängen von Knoten zu
# Knoten abfällt
buses_in_x = []
for i in range(1, 11):
    buses_in_x.append(ppt.get_bus_indices(str(i), net))
                      
fig_bus_volt, ax_bus_volt = plt.subplots(1, 1, figsize=(15,8))
for i in range(1, 11):
    volts = results_bus.loc['2020-01-01 18:00:00', buses_in_x[i-1]].values
    ax_bus_volt.plot(list(range(len(volts))), volts, '-x',
                     label=f'Verlauf der Spannung im Strang Nr. {i}')
    
ax_bus_volt.legend()
ax_bus_volt.grid()
ax_bus_volt.set_title('Verlauf der Spannung in den einzelnen Strängen')
ax_bus_volt.set_xlabel('Knoten Nr. ausgehend vom Transformator')
ax_bus_volt.set_ylabel('Spannung [V]')

#### Das Netwerk graphisch darstellen ########################################
# trace, die alle buses enthält, die eine Ladesäule haben
figure = pt.simple_plotly(net)

figure.add_trace(go.Scatter(x=net.bus_geodata.loc[choices, 'x'],
                            y=net.bus_geodata.loc[choices, 'y'],
                            mode='markers'))
figure.show()


