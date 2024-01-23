#!/usr/bin/env python
# coding: utf-8
#
# This code contains calculations for the so-called "remaining usable life" or "loss of life" equations
# contained in IEEE C57.91.  The equations approximate only thermal aging processes based on accelerated aging experiments
# in labratory conditions.
#
# This file is part of IEEE C57.91 2024 project which is released under BSD-3-Clause.
# See file LICENSE.md or go to https://opensource.ieee.org/inslife/ieee-c57.91-2024/ for full license details.

from scipy import integrate
import numpy as np
from .data_classes import Transformer, LoadConditions
from .constants import ageing_A, ageing_B

def estimate_loss_of_life(T_hs_input,time_input,T_reference=110,B=15000.,A=9.8E-18,nominal_insulation_life=180000,TUK=True):    
    # Section 5
    
    # Convert from Celcius to Kelvin
    T_hs_input = T_hs_input + 273.15
    T_reference = T_reference + 273.15
    
    time_input = time_input / 60. # convert minutes to hours
    
    # Modified to determine equivalent aging in hours
    # Time interval of accelerated aging determined by temperature profile being above rated temperature.
    
    per_unit_life = A*np.exp(B/T_hs_input)
    
    if TUK:
        # equations for thermally upgraded paper (TUK)
        V = np.exp((B/T_reference) - (B/T_hs_input))
    else:
        # equations for plain kraft paper (not TUK)
        V = 2**((T_hs_input-98.)/6.)
    
    dt = np.diff(time_input, prepend=-1)
    
    V_dt = integrate.cumulative_trapezoid(V*dt, initial=V[0])
    
    F_eqa = V_dt / integrate.cumulative_trapezoid(dt, initial=dt[0])
    
    loss_of_life = (F_eqa*time_input)*100/nominal_insulation_life
    
    return per_unit_life, V, F_eqa, loss_of_life


def solve_estimated_loss_of_life(Transformer,LoadConditions):
    
    A = ageing_A.get(Transformer.liquid_type.lower(),9.8E-18)
    B = ageing_B.get(Transformer.liquid_type.lower(),15000.)

    if Transformer.solution is not None:
        per_unit_life, V, F_eqa, loss_of_life = estimate_loss_of_life(
            Transformer.solution['Hot Spot [C]'].values,
            Transformer.solution['Time [Minutes]'].values,
            T_reference=Transformer.T_hsr+Transformer.T_ambr,
            TUK=Transformer.TUK,
            A=A,
            B=B,
        )
    else:
        raise Exception("Calculate temperatures first")
        
    Transformer.solution['Est. Aging Rate'] = V
    Transformer.solution['Est. Equivalent Aging Factor'] = F_eqa
    Transformer.solution['Est. Loss of Life'] = loss_of_life

    return Transformer