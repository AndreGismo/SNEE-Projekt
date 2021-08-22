# -*- coding: utf-8 -*-
"""
Created on Tue May 18 09:45:33 2021

@author: andre
Kerber-Netz simulieren über time series
kann es sein, dass bei den drei controllern irgendwelche überschneidungen beim
Eintragen der einzelnen Werte aus ihrem jeweilgen datasource in die loads vom net
gibt? nicht jeder Knoten hat im net[res_bus] eine Leistung anliegen (???)
=>vielleicht am level etwas ändern vom BatteryController?

----------------------------------------
bei Ladesäulen mit 22kW steigt die Leistung weiter nach dem Einschalten
=> müsste ja eigentlich sinken!!
=> irgendwas mit der P(SOC)-Formel (vielleicht passt das verhältnis von power/p_ls
                                    nicht mehr?)

bestes Regelergebnis (geringtste Spnnungsband-Verletzungen): 312
F_end = 0.4, U_start = 0.01, U_end = 0.06, ki = 0.5, vals_to_sum = 15, kd = 0
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
from scenario import Scenario
from battery_controller import BatteryController
from controllable_battery import ControllableBattery

#### zeitliche Auflösung der Simulation ######################################
resolution = '1min'

#### Variablen zum Steuern der simulierten Szenarien #########################
# Ankunftszeit (in Viertelstunden => 0800 wäre 32)
same_arrival = True
arrival_time = 46

same_power = True
loading_power = 11.1

same_travelled = True
distance_travelled = 200

# macht nur Sinn, einen der beiden auf True zu setzen
far_from_trafo = False
near_trafo = False

# soll geregelt werden?
controlling = True

# wie hoch ist der PowerFactor der Haushalte?
cosphi = 0.9

#Regelparameter für die Ladesäule einstellen
ControllableBattery.set_control_params('Ki', 0.5)
ControllableBattery.set_control_params('Kd', 0.1)

#### Netz bauen ##############################################################
# leeres Netz erzeugen
net = pn.create_kerber_vorstadtnetz_kabel_1()

#### Szenario erzeugen #######################################################
fun_scenario = Scenario.load_scenario('Szenario100')
fun_scenario.set_resolution(resolution)

if same_arrival:
    fun_scenario.set_constant('time of arrival', arrival_time, inplace=True)
    #fun_scenario.set_constant('time of arrival', 60, [22,70,80], inplace=True)
    
if same_power:
    fun_scenario.set_constant('charging power [kW]', loading_power, inplace=True)
    #fun_scenario.set_constant('charging power [kW]', 33, [20], inplace=True)

    
if same_travelled:
    fun_scenario.set_constant('distance travelled [km]', distance_travelled,
                              inplace=True)

if near_trafo:    
    fun_scenario.distribute_loads(inplace=True, near_trafo=True)
    
if far_from_trafo:
    fun_scenario.distribute_loads(inplace=True, near_trafo=False)
    
#### Daten für die einzelnen loads erzeugen (96, 146) ########################
# das sind die Daten vom 13.12.2020, weil es da den höchsten peak gab
data_nuernberg = pd.read_csv('Daten/Lastprofil/Nuernberg_absolut_final.csv')

# nur bestimmten Zeitraum (nicht kompletten Tag) simulieren:
data_nuernberg = ppt.set_simulation_range(data_nuernberg)

baseload = ppt.prepare_baseload(data_nuernberg, net, resolution)

batteries, datasource_bat = ppt.prepare_batteries(net, fun_scenario, resolution)

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
timeseries.run_timeseries(net)

#### Die Ergebnisse wieder in ein DF einlesen ################################
results_bus = pd.read_csv('res_bus/vm_pu.csv', sep=';')*400
results_trafo = pd.read_csv('res_trafo/loading_percent.csv', sep=';')
results_line = pd.read_csv('res_line/loading_percent.csv', sep=';')

results_bus.index = pd.date_range(start='2020', freq='15min',
                                  periods=len(results_bus))

results_line.index = pd.date_range(start='2020', freq='15min',
                                  periods=len(results_bus))

results_trafo.index = pd.date_range(start='2020', freq='15min',
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


fig_trafo, ax_trafo = plt.subplots(1, 1, figsize=(15, 8))
ax_trafo.plot(results_trafo.iloc[:, 1])
ax_trafo.set_xlabel('Zeitpunkt')
ax_trafo.set_ylabel('Auslastung [%]')


# samples = 10
# fig_load, ax_load = plt.subplots(1, 1, figsize=(15, 8))
# ax_load.plot(scenario_data[np.random.choice(scenario_data.columns, samples)]*1000,
#              '-x')
# ax_load.set_title('Profile von {} zufällig ausgewählte Lasten'.format(samples))
# ax_load.grid()
# ax_load.set_xlabel('Zeitpunkt [MM-TT hh]')
# ax_load.set_ylabel('Leistung [kW]')


# Zeichnen, wie die Spannung über den einzelnen Strängen von Knoten zu
# Knoten abfällt
buses_in_x = []
for i in range(1, 11):
    buses_in_x.append(ppt.get_bus_indices(str(i), net))
                      
fig_bus_volt, ax_bus_volt = plt.subplots(1, 1, figsize=(15,8))
for i in range(1, 11):
    volts = results_bus.loc['2020-01-01 19:30:00', buses_in_x[i-1]].values
    ax_bus_volt.plot(list(range(len(volts))), volts, '-x',
                      label=f'Verlauf der Spannung im Strang Nr. {i}')
    
ax_bus_volt.legend()
ax_bus_volt.grid()
ax_bus_volt.set_title('Verlauf der Spannung in den einzelnen Strängen')
ax_bus_volt.set_xlabel('Knoten Nr. ausgehend vom Transformator')
ax_bus_volt.set_ylabel('Spannung [V]')

### Das Netwerk graphisch darstellen ########################################
# trace, die alle buses enthält, die eine Ladesäule haben
# figure = pt.simple_plotly(net)

# charger_buses = fun_scenario.scenario_data['according bus nr.'].values
# figure.add_trace(go.Scatter(x=net.bus_geodata.loc[charger_buses, 'x'],
#                             y=net.bus_geodata.loc[charger_buses, 'y'],
#                             mode='markers'))
# figure.show()

violations = load_controller_bat.get_voltage_violations()
violated_buses = load_controller_bat.get_violated_buses()
print('Anzahl der Spannungsband-Verletzungen: {}'.format(violations))
print('\nUnd die betroffenen buses: \n {}'.format(violated_buses))

