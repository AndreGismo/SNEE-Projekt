(distributions)= 
# Methodology for Research


In this chapter the methodology used for investigating the influences of BEV loading on the local grid is beeing discussed. This methodology is separated into 7 parts:

- choosing and implementing a reference grid
- choosing and implementing of a standard load profile (SLP) for the households
- implementing a model for charging of BEV battery
- choosing and implementig of a distribution of arrival times for BEVs
- choosing and implementing of a distribution for the travelled distances
- choosing and implementing of a distribution for the nominal powers of the charging stations
- additionally a controller is beeing designed


## The Reference Grid





The reference grid used for the simulation is a [kerber network](https://pandapower.readthedocs.io/en/develop/networks/kerber.html) as it is provided by _pandapower_. The following [Figure 2](fig2) shows a schematic plot of the grid:

```{figure} https://pandapower.readthedocs.io/en/develop/_images/kerber_vorstadtnetz_a.PNG
:name: fig2
:width: 700px
The kerber network used for simulation
```

This network represents the average network in German suburbs as derived in {cite:p}`kerber_aufnahmefahigkeit_2011`. All the loads attached are households.


## The Standard Load Profile


As a SLP serves a profile "H0A" of [N_ERGIE netz](https://www.n-ergie-netz.de/startseite/produkte-dienstleistungen/netznutzung/netznutzung-strom/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8zifT2dDQyd_A18DfzCzAwCXQ0Ng52Ngg39jMz0w_EpMDY114-iRL-lGXH6DVCAo4FTkJGTsYGBu78ROfqRTaLI_SAFUfiND9ePwmuFsxF-BeAgxqvA0piQAjOoAnyhSMgfBbmhQBBhkOmZ6QkA7tlcaw!!/dz/d5/L2dBISEvZ0FBIS9nQSEh/) of 2020, which represents the load of a household. The day with the highest power demand is the 13.12.2020. This day was choosen for the simulation. The following [Figure 3](fig3) shows the SLP:

```{figure} img/slp.png
:name: fig3
:width: 700px
Load profile of the used SLP
```

The values are considered to be real power.


## The Model for charging BEV battery


The charging of the BEV battery is modelled according to {cite:p}`schuster_batterie-_2008` wich is given by the following equations:

```{math}
:label: eq1
P(SOC) = P_{max} \cdot e^{\left ( \tfrac{s - SOC}{k_L} \right )}
```

```{math}
:label: eq2
k_L = \frac{100-s}{ln (\frac{P_{max}}{P_{LS}})}
```

```{math}
:label: eq3
P_{LS} = \frac{U_{LS}}{U_N} \cdot I_{LS} \cdot E_{nom}
```

With the symbols beeing:

|Symbol|Meaning|Unit|
|--|--|--|
|$P$|Power|$W$|
|$P_{max}$|Maximum Power|$W$|
|$s$|Switching Point|$\%$|
|$SOC$|State of Charge|$\%$|
|$U_{LS}$|Load-stop Voltage|$V$|
|$U_N$|Nominal Voltage|$V$|
|$I_{LS}$|Load-stop Current|$\frac{1}{h}$|
|$E_N$|Nominal Energy|Wh|

The Nominal Voltage of Lithium-Ion-Batteries is expected to be $U_N= 3.9V$, the Load-stop Voltage is taken as $U_{LS}=4.2V$, the Load-stop Current is taken as $I_{LS} = 0.03 \frac{1}{h}$ (c-rate) and the Switching Point is taken as $s = 80\%$.

The following [Figure 4](fig4) shows the loading curve as described by Equation [Equation 1](eq1):

```{figure} img/psoc.png
:name: fig4
:width: 700px
Characteristic of the BEV batteries loading
```

It is to see, that the initial charging power is determined by the initial state of charge $SOC_0$, which is calculated in dependence of the travelled distance $d$ and the consumption $c$ according the following Equation [Equation 4](eq4):

```{math}
:label: eq4
SOC_0 = \frac{E_N - d \cdot c}{E_N} \cdot 100\%
```

The state of charge in the next discrete timestep $SOC_{n+1}$ is calculated in dependence of the timestep $\Delta t$ according the next Equation [Equation5](eq5):

```{math}
:label: eq5
SOC_{n+1} = SOC_n + P(SOC_n) \cdot \Delta t
```


## The Distribution of Arrival Times


The distribution of arrival times is beeing adopted from {cite:p}`Doum_Notw_2015`. The following [Figure 5](fig5) shows the distribution:

```{figure} img/dist.png
:name: fig5
:width: 700px
Distribution of the arrival time {cite:p}`Doum_Notw_2015`
```

It ist to see, that most people arrive at 18:00 and there is also another peak at 22:00.


## The Distribution of travelled Distances


The distribution of the travelled distances is taken from {cite:p}`statista_jahrliche_2021`. The vaues provided for 2020 are downscaled to one day (assuming 365 days driving per year). These downscaled values are given in the following table:

|Distance travelled [km]|Probability [-]|
|--|--|
|7|0.13|
|21|0.29|
|35|0.30|
|50|0.15|
|60|0.13|

These values determine the $d$ in Equation [](eq4). Furthermore the mean consumption of BEVs is taken as $c=17.7 \frac{kWh}{100km}$ and the battery capacity as $E_{nom}=52kWh$ (Values of the most sold BEV {cite:p}`ADAC_elektroautos_2021` according to {cite:p}`Renault_renault_2021`).


## The Distribution of the Nominal Power of the Charging Stations


The distribution is taken from {cite:p}`goel_stromtankstellen_nodate`, only taken into account the first three categories. This results in the values given in the following table:

|Charging power [kW]|probability|
|--|--|
|3.7|0.35|
|11.1|0.55|
|22.2|0.10|

Thee values determine the $P_{max}$ in Equation [](eq1).


(controlling_paragraph)=
## The controller


As a controller serves as a $P(U)$ controlling according the characteristic in the following [Figure 6](fig6):

```{figure} img/controller.png
:name: fig6
:width: 700px
Characteristic of the controller
```

The characteristic represents the P-element of the controller. The voltage drop $\Delta U$ is defied according Equation [Equation 6](eq6):

```{math}
:label: eq6
\Delta U = \frac{400V - U_{node}}{400V} \cdot 100\%
```

Furthermore an I-element is used defined in Equation [](eq7):

```{math}
:label: eq7
F_I = K_I \cdot \sum_{t-n}^{t} \Delta U(t)
```

And additionally a D-Element contributes to the controller according to Equation [](eq8):

```{math}
:label: eq8
F_D = K_D \cdot (\Delta U (t) - \Delta U (t-1))
```

This results in a controlled power $P_{control}$ according to Equation [](eq9):

```{math}
:label: eq9
P_{control} = P \cdot (F - F_D - F_I)
```

The complete control loop is shown in the following [Figure 7](fig7)

```{figure} img/control-loop.png
:name: fig7
:width: 700px
Controller loop
```


# Bibliography


```{bibliography}
:filter: docname in docnames
```
