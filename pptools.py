# -*- coding: utf-8 -*-
"""
Created on Tue May 18 15:23:03 2021

@author: andre
pptools: Hilfsfunktionen zum Arbeiten mit pandapower
np.roll zum variieren der Zeit, wann der Ladevorgang beginnt
"""
import numpy as np
import pandas as pd


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


def apply_scenario(df, net, P_load, load_start, load_duration, every_nth):
    '''
    Verändert das DataFrame "df" derart, dass jeder "every_nth"-te Haushalt
    im Netz "net" ein E-Fahrzeug bekommt. Der Ladevorgang beginnt zur Uhrzeit
    "load_start" und dauert "load_duration" Stunden und hat eine Leistung von
    "P_load" MW.

    Parameters
    ----------
    df : pandas DataFrame
        Das DataFame, das die Lastprofile für die loads enthält.
    net : pandapowerNet
        Das Netz, in dem das Szenario betrachtet wird
    P_load : float
        Die Ladeleistung der E-Fahrzeuge in MW
    load_start : int
        Die Uhrzeit (hh), wann der Ladevorgang beginnt
    load_duration : int
        Die Dauer (in Stunden) des Ladevorgangs
    every_nth : int
        Die Angabe, jeder wievielte Haushalt ein E-Fahrzeug bekommt

    Returns
    -------
    entsprechend der Vorgabe geändertes DataFrame (Leistungen in MW)

    '''
                              
    load_start *= 4
    load_duration *= 4
    load_end = load_start+load_duration
    
    filt_rows = (df.index >= load_start) & (df.index <= load_end)
    filt_cols = [i for i in range(1, len(df.columns)-1) if i % every_nth == 0]
    df.loc[filt_rows, filt_cols] += P_load
        
    # Spalten umbenennen, dass später der controler klarkommt
    df.columns=net.load.index
    
    return df


def add_ecars(df, net, profile, every_nth):
    filt_cols = [i for i in range(1, len(df.columns)-1) if i % every_nth == 0]
    df.loc[:, filt_cols] += profile
        
    # Spalten umbenennen, dass später der controler klarkommt
    df.columns=net.load.index
    
    return df


def add_emobility(df, net, profile, penetration):
    '''
    load_profile = pptools.add_emobility(load_profile, net, e_profile, penetration)
    
    Überlagert 'penetration' Prozent der Lasten des Netzes 'net' in
    'load_profile' mit dem Lastprofil 'e_profile'

    Parameters
    ----------
    df : pandas DataFrame
        Das DataFrame, welches alle Lastprofile aller loads im Netz enthält
    net : pandapowerNet
        Das Netz, welches die Lasten enthält
    e_profile : pandas DataFrame
        Das Lastprofil der Ladesäulen
    penetration : int
        Durchdringung [%] der Ladesäulen

    Raises
    ------
    ValueError
        Wenn für 'penetration' eine Zahl größer als 100 übergeben wird

    Returns
    -------
    df : pandas DataFrame
        Das entsprechend der Vorgabe erweiterte DataFrame

    '''
    if penetration > 100:
        raise ValueError("'penetration' darf maximal gleich 100 sein.")
    df.columns = net.load.index
    loads = len(net.load.index)
    loads_to_add = int(np.round(penetration/100*loads, 0))
    loads_available = list(net.load.index)
    # zum Nachverfolgen, welche loads (also deren zugehöriger bus)
    # gewählt worden sind
    choosen_bus = []
    for i in range(loads_to_add):
        choice = np.random.choice(loads_available)
        # sicherstellen, dass nicht mehrmals dieselbe load gewählt wird
        choosen = loads_available.pop(loads_available.index(choice))
        # den der gewählten load entsprechenden bus bestimmen
        according_bus = net.bus.index[net.load.loc[choosen, 'bus']]
        choosen_bus.append(according_bus)
        #Profil vom Ladevorgang überlagern
        df.loc[:, [choice]] += profile.iloc[:].values
    return choosen_bus


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
    
        
    