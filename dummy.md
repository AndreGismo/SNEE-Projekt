# Methodology for Research


In this chapter the methodology used for investigating the influences of BEV loading on the local grid is beeing discussed. This methodology is separated into 4 parts:

- choosing and implementing a reference grid
- choosing and implementing of a standard load profile (SLP) for the households
- implementing a model for charging of BEV battery
- choosing and implementig of a distribution of arrival times for BEVs


## The Reference Grid





The reference grid used for the simulation is a [kerber network](https://pandapower.readthedocs.io/en/develop/networks/kerber.html) as it is provided by _pandapower_. The following [Figure 2](fig2) shows a schematic plot of the grid:

```{figure} https://pandapower.readthedocs.io/en/develop/_images/kerber_vorstadtnetz_a.PNG
:name: fig2
:width: 700px
The kerber network used for simulation
```

This network represents the average network in German suburbs as derived in Kerbers doctoral thesis. All the loads attached are households.


## The Standard Load Profile


As a SLP serves a profile "H0A" of [N_ERGIE netz](https://www.n-ergie-netz.de/startseite/produkte-dienstleistungen/netznutzung/netznutzung-strom/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8zifT2dDQyd_A18DfzCzAwCXQ0Ng52Ngg39jMz0w_EpMDY114-iRL-lGXH6DVCAo4FTkJGTsYGBu78ROfqRTaLI_SAFUfiND9ePwmuFsxF-BeAgxqvA0piQAjOoAnyhSMgfBbmhQBBhkOmZ6QkA7tlcaw!!/dz/d5/L2dBISEvZ0FBIS9nQSEh/) of 2020. The day with the highest power demand is the 13.12.2020. This day was choosen for the simulation. The following [Figure 3](fig3) shows the SLP:

```{figure} img/slp.png
:name: fig3
:width: 700px
Load profile of the used SLP
```


## The Model for charging BEV battery


The charging of the BEV battery is modelled according to Schneiders diploma thesis wich is given by the following equations:

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

The following [Figure 4](fig4) shows the loading curve as described by [Equation 1](eq1):

```{figure} img/psoc.png
:name: fig4
:width: 700px
Characteristic of the BEV batteries loading
```
