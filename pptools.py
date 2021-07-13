# -*- coding: utf-8 -*-
"""
Created on Tue May 18 15:23:03 2021

@author: andre
pptools: Hilfsfunktionen zum Arbeiten mit pandapower
np.roll zum variieren der Zeit, wann der Ladevorgang beginnt
"""
import numpy as np
import pandas as pd
import battery as bat
import pickle
from controllable_battery import ControllableBattery


def scale_df(df, consumption_year):
    '''
    Skaliert das DataFrame df derart, dass über ein gesamtes Jahr der
    vorgegebene Jahresverbrauch consumption_year (in kWh) zustandekommt.

    Parameters
    ----------
    df : pandas DataFrame
        Das DataFame, das die Lastprofile für die loads enthält.
    consumption_year : float
        Der gewünschte Jahresverbrauch

    Returns
    -------
    entsprechend der Vorgabe skaliertes DataFrame (Leistungen in MW)

    '''
    #return df / (df[df.columns[0]].sum() * 365)* consumption_year
    return df / 1e9 * consumption_year


def prepare_baseload(df, net):
    data = df.copy()
    if 'Unnamed: 0' in data.columns:
        data.drop('Unnamed: 0', axis=1, inplace=True)
        
    for i in range(1, len(net.load)):
        data[i] = data[data.columns[0]]
        
    data.columns = net.load.index
    data /= 1e6
    return data


def prepare_batteries(net, scenario):
    batteries = []
    for i in scenario.scenario_data.index:
        e_bat = scenario.scenario_data.at[i, 'battery size [kWh]']
        p_load = scenario.scenario_data.at[i, 'charging power [kW]']
        dist_travelled = scenario.scenario_data.at[i, 'distance travelled [km]']
        consumption = scenario.scenario_data.at[i, 'consumption [kWh/100km]']
        arrival = scenario.scenario_data.at[i, 'time of arrival']
        at_load = scenario.scenario_data.at[i, 'load nr.']
        at_bus = scenario.scenario_data.at[i, 'according bus nr.']
        
        # eine entsprechende ControllableBattery erzeugen
        bat = ControllableBattery(net, at_load, at_bus, e_bat,
                                  p_load, dist_travelled, consumption, arrival)
        batteries.append(bat)
        
    columns = scenario.scenario_data['load nr.'].astype(int)
    datasource = pd.DataFrame(index=list(range(96)), columns=columns)
        
    return batteries, datasource # müssen an BatteryControler übergeben werden


def apply_scenario(df, net, scenario):
    data = df.copy()
    # DataFrame, welches nur die Daten Ladekurve der e-Fahrzeuge speichert
    data_ecar = pd.DataFrame()
    data.columns = net.load.index
    for i in scenario.scenario_data.index:
        e_bat = scenario.scenario_data.at[i, 'battery size [kWh]']
        p_load = scenario.scenario_data.at[i, 'charging power [kW]']
        dist_travelled = scenario.scenario_data.at[i, 'distance travelled [km]']
        consumption = scenario.scenario_data.at[i, 'consumption [kWh/100km]']
        arrival = scenario.scenario_data.at[i, 'time of arrival']
        load = scenario.scenario_data.at[i, 'load nr.']
        e_profile = calc_load_profile_ecar(e_bat, p_load, dist_travelled,
                                           consumption, arrival)
        
        data.loc[:, load] += e_profile.iloc[:, 0].values
        data_ecar[i] = e_profile.iloc[:, 0].values
        
    # damit die columns von data_ecar (welches ja später zur data-source wird)
    # int sind 
    new_columns = scenario.scenario_data['load nr.'].astype(int)
    data_ecar.columns = new_columns  
    data /= 1e6
    data_ecar /= 1e6
    return data, data_ecar


def add_emobility_like_scenario(df, net, scenario):
    df.columns = net.load.index
    for i in scenario.index:
        eprofile = calc_load_profile_ecar(50, scenario.at[i, 'p_load [kW]'],
                                          scenario.at[i, 'travelled [km]'], 20,
                                          scenario.at[i, 'arrival'])
        at_bus = scenario.at[i, 'bus']
        df.loc[:, [at_bus]] = eprofile.iloc[:].values
        
    return list(scenario.loc[:, 'bus'])
    


def get_critical_bus(results_bus):
    '''
    Findet den Index von demjenigen Bus mit der höchsten Belastung (also dem
    größten Spannungseinbruch) in "results_bus"

    Parameters
    ----------
    results_bus : pandas DataFrame
        Das DataFrame, das die Ergebnisse der Knotenspannungen enthält

    Returns
    -------
    int
        Index vom höchstbelasteten Knoten

    '''
    min_voltages = []
    for col in results_bus.columns:
        min_voltages.append(results_bus.loc[:, col].min())
        
    min_voltages = np.array(min_voltages)
    return min_voltages[1:].argmin()


def get_critical_line(results_line):
    '''
    Findet den Index von derjenigen Leitung mit der höchsten Belastung (also
    der höchsten Auslastung) in "results_line"

    Parameters
    ----------
    results_line : pandas DataFrame
        Das DataFrame, welches die Ergebnisse der Leitungsauslastungen enthält

    Returns
    -------
    int
        Index der höchstbelasteten Leitung

    '''
    max_loadings = []
    for col in results_line.columns:
        max_loadings.append(results_line.loc[:, col].max())
        
    max_loadings = np.array(max_loadings)
    return max_loadings[1:].argmax()
    


def extract_above(df, threshold):
    '''
    Erzeugt ein DataFrame welches nur die Spitzen des Lastprofils von "df",
    welche oberhalb der Grenzleistung "threshold" liegen, enthält
    (der Rest ist 0).

    Parameters
    ----------
    df : pandas DataFrame
        Das DataFrame mit dem Lastprofil
    threshold : int
        Grenzleistung (MW)

    Returns
    -------
    data : pandas DataFrame
        Ein DataFrame, welches nur diejenigen Teile des Lastprofils von "df"
        enthält, die oberhalb von "threshold" liegen.

    '''
    data = df.copy()
    filt = data[data.columns[0]] <= threshold
    data.loc[filt] = 0
    data -= threshold
    filt = data[data.columns[0]] <= 0
    data.loc[filt] = 0
    return data
    

def limit_to(df, limit):
    data = df.copy()
    filt = data[data.columns[0]] >= limit
    data.loc[filt] = limit
    return (data)


def shift_profile(df, steps):
    '''
    Verschiebt das Lastprofil von "df" um "steps" Zeitschritte.

    Parameters
    ----------
    df : pandas DataFrame
        DataFrame containing a load profile
    steps : int
        Number of time steps to shift "df"

    Returns
    -------
    data : pandas DataFrame
        A DataFrame holding the same load profile as "df", just shiftet by 
        "steps"

    '''
    shifted = np.roll(df.values, steps)
    data = pd.DataFrame(shifted)
    data.index = df.index
    data.columns = df.columns
    return data


def add_random(df, smoothing_width):
    '''
    Überlagert das Lastprofil vom DataFrame "df" mit Zufallszahlen. Um einen
    zu steilen Lastgradienten zu verhindern, kann mit "smoothing_width"
    angegeben werden, wie sehr die resultierende Kurve geglättet werden soll

    Parameters
    ----------
    df : pandas DataFrame
        Das DataFrame, welches das Lastprofil enthält
    smoothing_width : int
        Die Anzahl benachbarter Werte, die zur Berechnung des gleitenden
        Mittels herangezogen werden (muss eine ungerade Zahl sein)

    Raises
    ------
    ValueError
        Wenn eine gerade Zahl für "smoohing_width" übergeben wird

    Returns
    -------
    rand_df : pandas DataFrame
        Ein DataFRame, welches das mit Zufallszahlen überlagerte Lastprofil
        enthält

    '''
    if not smoothing_width == 0:
        if (smoothing_width % 2 == 0):
            raise ValueError("'smoothing_width' muss eine ungerade ganze Zahl sein")
    rand = 200*np.random.rand(len(df.index)+smoothing_width-1)-100
    rand_df = pd.DataFrame(rand)
    if not smoothing_width == 0:
        rand_df = rand_df.rolling(window=smoothing_width, center=True).mean()
        first_elements = int((smoothing_width-1)/2)
        rand_df = rand_df.iloc[first_elements:-first_elements]
        rand_df.index = df.index
    rand_df.loc[:, rand_df.columns[0]] += df.loc[:, df.columns[0]]
    return rand_df


def randomize_load(df, **kwargs):
    if len(kwargs) == 0:
        kwargs['steps'] = np.random.randint(-8, 8)
        kwargs['smoothing_width'] = 31
    data = shift_profile(df, kwargs['steps'])
    data = add_random(data, kwargs['smoothing_width'])
    return data


def get_bus_indices(line, net):
    '''
    

    Parameters
    ----------
    line : string
        Der Netzstrahl, von dessen Knoten die Indizes bestimmt werden sollen
    net : pandapowerNet
        Das Netz in dem sich der Strang befindet

    Returns
    -------
    bus_indices : list
        Eine Liste, die alle Indizes der Knoten auf dem Strang enthält

    '''
    bus_indices = []
    # der Index der main busbar, bei der jeder Strang beginnt
    bus_indices.append(str(1))
    for num, bus in enumerate(net.bus['name']):
        if bus.count('_' + line + '_') == 1 and bus.count('load') == 0:
            bus_indices.append(str(net.bus['name'].index[num]))
            
    return bus_indices


def calc_load_profile_ecar(e_bat, p_const, dist_trav, consumption, arrival):
    battery = bat.Battery(e_bat, p_const)
    energy_used = dist_trav*consumption/100
    energy_start = e_bat - energy_used
    profile = battery.calc_load_profile(energy_start)
    profile = np.roll(profile, arrival)
    profile = pd.DataFrame(profile)
    return profile * 1000


def save_scenario(scenario, filename):
    path = 'Daten/Szenarien/' + filename + '.pkl'
    with open(path, 'wb') as output:
        pickle.dump(scenario, output)
        
        
def load_scenario(filename):
    path = 'Daten/Szenarien/' + filename + '.pkl'
    with open(path, 'rb') as source:
        scenario = pickle.load(source)
    return scenario
    
    
        
    