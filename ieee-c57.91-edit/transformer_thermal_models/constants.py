#!/usr/bin/env python
# coding: utf-8
#
# This code contains constants values for specific materials, cooling modes, or physics used throughout the source code. 
#
# This file is part of IEEE C57.91 2024 project which is released under BSD-3-Clause.
# See file LICENSE.md or go to https://opensource.ieee.org/inslife/ieee-c57.91-2024/ for full license details.

# Table G.2
specific_heat = {
    "steel":3.51,
    "copper":2.91,
    "aluminum":6.80,
    "mineral oil":13.92,
}

#Table G.2
G_table = {
    "mineral oil":2797.3,
}

#Table G.2
D_table = {
    "mineral oil":0.0013573,
}

#Cooling mode exponenets for Old C7 and Alt C7
m_exponent = {
    # m; [1]
    "ONAN":0.8,
    "ONAF":0.8,
    "OFAF":0.8,
    "ODAF":1.0,
}

n_exponent = {
    # n; [1]
    "ONAN":0.8,
    "ONAF":0.9,
    "OFAF":0.8,
    "ODAF":1.0,
}

## Added by Tim
liquid_density = {
    "mineral oil":6.68, # [lb/gal]
}

#Table G.3
duct_liquid_rise_exponent = {
    # x; [1]
    "ONAN":0.5,
    "ONAF":0.5,
    "OFAF":0.5,
    "ODAF":1.0,
}

#Table G.3
average_liquid_rise_exponent = {
    # y; [1]
    "ONAN":0.8,
    "ONAF":0.9,
    "OFAF":0.9,
    "ODAF":1.0,
}

#Table G.3
to_bo_rise_exponent = {
    # z; [1]
    "ONAN":0.5,
    "ONAF":0.5,
    "OFAF":1.0,
    "ODAF":1.0,
}

#Ageing rate constants

ageing_A = {
    "mineral oil": 9.8E-18, # based on loading guide average of several experiments
}

ageing_B = {
    "mineral oil": 15000, # based on loading guide average of several experiments 
}