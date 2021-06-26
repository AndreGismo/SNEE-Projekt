# -*- coding: utf-8 -*-
"""
Created on Sat Jun 19 10:05:34 2021

@author: andre
ein smarter Controller für die Batterien (also für denjenigen Teil vom Last-
profil, der von der battery kommt)
"""

import pandapower as pp
from pandapower import control
import pandas as pd
from pandapower import timeseries as ts


class BatteryController(control.controller.const_control.ConstControl):
    """
        Example class of a Battery-Controller. Models an abstract energy storage.
    """
    def __init__(self, net, baseload, element, variable, element_index, data_source=None,
                 in_service=True, recycle=False, order=-1, level=-1, **kwargs):
        super().__init__(net, in_service=in_service, recycle=recycle, data_source=data_source,
                         element_index=element_index, order=order, level=level,
                         element=element, variable=variable,
                         initial_powerflow = True, **kwargs)
        # baseload, die nur die SLPs von den Haushalten enthält
        self.baseload = baseload * 1e-6
        self.battery_loads = self.data_source.df.copy()
        # 
        for i in self.data_source.df.columns:
            self.battery_loads.loc[:, i] = self.data_source.df.loc[:, i].values -\
                self.baseload.loc[:, i].values
                
    def _write_with_loc(self, net):
        super._write_with_loc(net)
        net[self.element].loc[self.element_index, self.variable] += 1
        