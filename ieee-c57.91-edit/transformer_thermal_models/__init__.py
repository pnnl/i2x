#!/usr/bin/env python
# coding: utf-8
#
# This code initializes the python module for thermal modeling of transformers.  
# Other helper functions are included that may be used in multiple locations
#
# This file is part of IEEE C57.91 2024 project which is released under BSD-3-Clause.
# See file LICENSE.md or go to https://opensource.ieee.org/inslife/ieee-c57.91-2024/ for full license details.

from .data_classes import Transformer, LoadConditions, export_data

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d

from datetime import datetime
from argparse import Namespace
import time as pyt

from .plotting import plot_results, plot_max_hotspot
from .methods import solve_temperatures, AVAILABLE_METHODS
from .ageing import estimate_loss_of_life, solve_estimated_loss_of_life
    
def bubble_inception_temperture(WCP,liquid_head_pressure,gas_headspace_pressure,A=2.173E-7,B=4722.8,n=1.4959):

    # P_tot in units of mmHq
    # WCP in units of X %

    P_tot = liquid_head_pressure + gas_headspace_pressure
    
    #C57.91 Annex A Eq A.2
    T_bubble = ( (n*B) / (n*np.log(1/A) + n*np.log(WCP) - np.log(P_tot)) ) - 273.15

    return T_bubble


def liquid_head_pressure(depth,liquid_density):

    # depth in meters
    # liquid_density in kg/(m^3)

    P_to_mmHg = 0.00750062 # Pascals to mmHq
    g = 9.80655 # gravitational acceleration constant

    #C57.91 Annex A Eq. A.4
    return depth * liquid_density * g * P_to_mmHg

def solve_max_hotspot(Transformer,base_load,min_load,max_load,load_step,low_avg_temp,high_avg_temp,temp_step,time_interval,method):
    
    # time_interval in minutes
    
    test_load = np.round(np.arange(min_load, max_load+load_step, load_step), 3)
    test_ambient = np.round(np.arange(low_avg_temp, high_avg_temp+temp_step, temp_step), 2)

    max_hotspot_table = np.ndarray((len(test_load),len(test_ambient)))
    
    selected_method = AVAILABLE_METHODS.get(method, None)
    
    if not selected_method:
        assert False, method + '" method not supported.'
    
    for i,l in enumerate(test_load):
        for j,t in enumerate(test_ambient):
            #print("Solving for... load: "+str(l)+", ambient temp: "+str(t))
            # inject a step function of load into the transformer model for a given average ambient temperature
            conditions = LoadConditions()
            conditions.time = [0,2159,2160,2160+time_interval,2161+time_interval,4320]
            conditions.T_ambient = [t,t,t,t,t,t]
            conditions.load = [base_load,base_load,l,l,base_load,base_load]
            conditions.update_profiles()
        
            solution = selected_method(Transformer,conditions)
            
            max_hotspot_table[i,j] = np.round(np.nanmax(solution['Hot Spot [C]']),1)
            
    df = pd.DataFrame(max_hotspot_table,columns=test_ambient,index=test_load)
    
    output = {
        'Overload Time Interval':time_interval,
        'Max Hotspot Table':df,
        'Method':method,
        'Initial Load':base_load,
    }
            
    return output


