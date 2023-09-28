"""
A collection of methods and data for upgrade costs.
Note that these will be by necessity rough, but the idea is to have
a framework that is relatively easy to alter and get to the better numbers
by altering the input data
"""

import pandas as pd
import numpy as np
import os


class TransformerCosts:
    def __init__(self):
        this_dir = os.path.split(__file__)[0]
        df = pd.read_csv(os.path.join(this_dir,"transformer_costs.csv"), skiprows=1)
        
        ## take the average cost for each phase/kVA combination
        self.df = df.groupby(["phases", "rated_kVA"])["total_cost"].aggregate(np.average)

    
    def get_cost(self, nphase, kva):
        idx = pd.IndexSlice[nphase]
        max_test = kva <= self.df.loc[idx].index.get_level_values("rated_kVA").max()
        min_test = kva >= self.df.loc[idx].index.get_level_values("rated_kVA").min()
        if max_test and min_test:
            # interporlation
            return np.interp(kva, 
                             self.df.loc[idx].index.get_level_values("rated_kVA"),
                             self.df.loc[idx].values)
        else:
            if not max_test:
                # linearly extrapolate largest two values
                vals = self.df.loc[idx].sort_index().iloc[-2:] # largest 2 values
            else:
                # linearly extrapolate smallest two values
                vals = self.df.loc[idx].sort_index().iloc[-2:] # largest 2 values
            return np.polyval(np.polyfit(vals.index, vals.values, 1), kva)
        

class ConductorCosts:
    def __init__(self):
        # data from PG&E Unit Cost Guid 2023: https://www.pge.com/pge_global/common/pdfs/for-our-business-partners/interconnection-renewables/Unit-Cost-Guide.pdf
        self.costs = {"oh" : (165 + 227)/2, #$/ft average of urban and rural OH line
                    "ug" : 268}

    def get_cost(self, typ, length, unit="ft"):
        """
        typ is 'oh' (Overhead line) or 'ug' (Underground Cable)
        """
        if typ not in ["oh", "ug"]:
            raise KeyError("ConductorCosts::get_cost: conductor typ must be 'oh' or 'ug'")
        if unit != "ft":
            length *= self.units2ft(unit)
        return length*self.costs[typ]
    
    def units2ft(self, u:str) -> float:
        """return a converstion factor from unit u to ft so that
        x[u] * factor = x[ft]
        """
        if u.lower() in ["km", "kilometer"]:
            return 3280.84
        if u.lower() in ["m", "meter"]:
            return 3.28084
        if u.lower() in ["yd", "yrd", "yard"]:
            return 3.0
        if u.lower() in ["mi", "mile", "miles"]:
            return 5280.0
        if u.lower() in ["foot", "feet"]:
            return 1.0

class RegulatorCosts:
    def __init__(self):
        # data from PG&E Unit Cost Guid 2023: https://www.pge.com/pge_global/common/pdfs/for-our-business-partners/interconnection-renewables/Unit-Cost-Guide.pdf 
        #   says ~222k
        # from NREL Distribution Unit Cost Database: Horowitz, Kelsey. 2019. ""2019 Distribution System Upgrade Unit Cost Database Current Version."" NREL Data Catalog. Golden, CO: National Renewable Energy Laboratory. Last updated: September 16, 2022. DOI: 10.7799/1491263."
        #   150k - 183 k
        # so go with 175k for now
        self.cost = {"new": 175000,
                     "settings": 2575 # from PG&E Unit Cost Guid 2023
        }
    
    def get_cost(self, typ):
        if typ not in ["new", "settings"]:
            raise KeyError("RegulatorCosts:get_cost: typ must be 'new' or 'settings'")
        return self.cost[typ]