#!/usr/bin/env python
# coding: utf-8
#
# This code contains the data class structures which contain properties nessacary for performing the models.
# Transformer class describes properties attributed to a specific thermal class of transformer.
# LoadConditions describes the time varying operational parameters the transformer experiences.
#
# This file is part of IEEE C57.91 2024 project which is released under BSD-3-Clause.
# See file LICENSE.md or go to https://opensource.ieee.org/inslife/ieee-c57.91-2024/ for full license details.

import numpy as np
from scipy.interpolate import interp1d
import json
import pandas as pd
import datetime

class Transformer():
    
    _thermal_properties = [
        'MVA_rated',
        'MVA_loss',
        'T_loss',
        'P_wr',
        'P_er',
        'P_sr',
        'P_cr',
        'P_coe',
        'E_hs',
        'M_cc',
        'M_tank',
        'liquid_volume',
        'T_ambr',
        'T_wg',
        'T_wr',
        'T_hsr',
        'T_tor',
        'T_bor',
        'T_k',
        'H_hs',
        'tau_w',
        'cooling_system',
        'winding_material',
        'liquid_type',
        'WCP',
        'T_bit',
        'gas_head_p',
        'TUK',
    ]
    
    def __init__(self):
        for p in self._thermal_properties:
            exec("self.%s = None" % p)
        
        # defining defualt values for testing
        self.MVA_rated = 52 # Rated MVA
        self.MVA_loss = 28 # MVA which losses were measured
        self.T_loss = 75 # temperature which losses were measured 
        self.P_wr = 51690 # winding I**2*R loss at rated load [W]
        self.P_er = 0 # eddy loss of windings at rated load [W]
        self.P_sr = 21078 # power in stray losses [W]
        self.P_cr = 36986 # power in core losses [W]
        self.P_coe = 36986 # power in core losses when overexcited (load > 1) [W]
        self.E_hs = 1 # [1]
        self.M_cc = 75600 # mass of core and coils [lb]
        self.M_tank = 31400 # mass of tank and fittings [lb]
        self.liquid_volume = 4910 # liquid volume [gal]
        self.T_ambr = 30.0 # temperature of ambient at rated load [C]
        self.T_wg = 65 # gaurantee rated temperature [C]
        self.T_wr = 63 # temperature of windings [C]
        self.T_hsr = 80 # temperature of hotspot at rated load [C]
        self.T_tor = 55 # temperature of top liquid at rated load [C]
        self.T_bor = 25 # temperature of bottom liquid at rated load [C]
        self.T_k = 234.5 # temperature correction for lossess of winding [C]
        self.H_hs = 1.0 # relative height of hotspot in windings [0-1]
        self.tau_w = 5.0 # winding time constant [min]
        self.cooling_system = 'ONAN' # type of cooling system
        self.winding_material = 'Copper' # type of winding conductor
        self.liquid_type = 'mineral oil' # type of liquid
        self.WCP = 2 # percent content of water in paper [%]
        self.gas_head_p = 760 # gas headspace pressure [mmHg]
        self.TUK = True # Does transformer have thermally upgraded paper?
        
        self.time_sol = None
        self.solution = None
        
    def to_json(self):
        output = dict()
        for p in self._thermal_properties:
            exec("output['%s'] = self.%s" % (p, p))
        return output
        
    def from_json(self,input_json_filename):
        with open(input_json_filename,'r') as f:
            input_json = json.loads(f.read())
        for p in self._thermal_properties:
            try:
                exec("self.%s = input_json['%s']" % (p, p))
            except KeyError:
                pass
        return self
    
    def solve_BIT(self):
    
        # FIXME: make liquid density consistent between thermal modeling and BIT
        liquid_density = 910

        liquid_head_p = liquid_head_pressure(self.bit_depth,liquid_density)

        T_bit = bubble_inception_temperture(
            self.WCP,
            liquid_head_p,
            self.gas_head_p,
        )

        self.T_bit = np.round(T_bit,1)

        return self
    

class LoadConditions():
    
    _load_conditions = [
        'time',
        'T_ambient',
        'load',
        'overexcited',
    ]
    
    def __init__(self):
        for p in self._load_conditions:
            exec("self.%s = None" % p)
            
        # Varaibles for solving and plotting
        self.T_ambient_profile = None
        self.Load_profile = None
        self.Overexcited_profile = None
        self.initial_datetime = None

    def to_json(self):
        output = dict()
        for p in self._load_conditions:
            exec("output['%s'] = self.%s" % (p, p))
        return output

    def update_profiles(self):
        # Required to interpolate/extrapolate input data for the differential solver to get data for an arbitrary time
        self.Load_profile = interp1d(self.time, self.load, kind='previous', fill_value='extrapolate')
        self.T_ambient_profile = interp1d(self.time, self.T_ambient, kind='linear', fill_value='extrapolate')

        if self.overexcited is not None:
            self.Overexcited_profile = interp1d(self.time, self.overexcited, kind='nearest', fill_value='extrapolate')
        else:
            self.Overexcited_profile = None
            
        return self
    
    def import_data(self,csv_file_name):
        df = pd.read_csv(csv_file_name,)

        if 'Time' in df.columns:
            time = pd.to_datetime(df['Time'])
            self.initial_datetime = time[0]
            time = (time-time[0]).apply(lambda x: x.total_seconds()/60.0).values
        elif 'Minutes' in df.columns:
            time = df['Minutes'].values
        elif 'Hours' in df.columns:
            time = df['Hours'].values
            time *= 60
        else:
            raise "'Time' or 'Minutes' or 'Hours' not found in CSV"

        if 'Ambient' in df.columns:
            T_ambient = df['Ambient'].values
        else:
            raise "'Ambient' temperature data not found in CSV"
        
        if 'Load' in df.columns:
            load = df['Load'].values
        else:
            raise "'Load' data not found in CSV"
            
        if 'Overexcited' in df.columns:
            overexcited = df['Overexcited'].values
        else:
            overexcited = None
            
        for p in self._load_conditions:
            exec("self.%s = %s" % (p, p))
            
        self.update_profiles()
            
        return self
    
def export_data(Transformer, LoadConditions):

    solution = Transformer.solution
    time = LoadConditions.time
    load = LoadConditions.load
    T_ambient = LoadConditions.T_ambient
    overexcited = LoadConditions.overexcited
    time_sol  = solution['Time [Minutes]']
    initial_dt = LoadConditions.initial_datetime

    new_output_table = pd.DataFrame()
    new_output_table['Time [Minutes]'] = np.transpose(time)   
    new_output_table['Load [1]'] = np.transpose(load)
    new_output_table['Ambient [C]'] = np.transpose(T_ambient)
    if overexcited is not None:
        new_output_table['Overexcited [1]'] = np.transpose(overexcited)
        
    #print(solution.columns.values)
    col_names = list(solution.columns.values)
    col_names.remove('Time [Minutes]')
    for col in col_names:
        data = solution[col]
        new_output_table[col] = (interp1d(time_sol,data,fill_value='extrapolate'))(time)

    new_output_table = new_output_table.interpolate()
    
    if initial_dt is not None:
        datetimes = [datetime.timedelta(minutes=m)+initial_dt for m in new_output_table['Time [Minutes]']]
        new_output_table['Time [Minutes]'] = datetimes
        new_output_table.rename(columns={'Time [Minutes]':'Time [Datetime]'},inplace=True)
    
    csv = new_output_table.to_csv(index=False,lineterminator='\r\n')
        
    return csv