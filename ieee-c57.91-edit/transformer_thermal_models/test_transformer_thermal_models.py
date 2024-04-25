#!/usr/bin/env python
# coding: utf-8
#
# This code contains unit tests for the temperature calculations, which ensure a basic level of sanity and functionality.
#
# This file is part of IEEE C57.91 2024 project which is released under BSD-3-Clause.
# See file LICENSE.md or go to https://opensource.ieee.org/inslife/ieee-c57.91-2024/ for full license details.


def execute_transformer_thermal_models(method):
    import transformer_thermal_models
    from transformer_thermal_models import Transformer, LoadConditions
    import numpy as np

    # Running a unit test to ensure that the thermal model converges to the 
    # rated hotspot temperature when fully loaded at ambient rated temperature

    #Load transformer data
    xfmr = Transformer()

    #Load loading conditions file
    lc = LoadConditions()
    lc.time = np.arange(0,1000)

    load = np.zeros(1000)
    load[10:] = 1
    lc.load = load

    T_ambient = [30] * 1000
    lc.T_ambient = T_ambient

    lc.update_profiles()

    transformer_thermal_models.methods.solve_temperatures(xfmr,lc,method)

    hotspot = xfmr.solution['Hot Spot [C]']
    top_oil = xfmr.solution['Top Liquid [C]']

    assert np.round(max(hotspot),0) == xfmr.T_hsr + xfmr.T_ambr, str(method)
    assert np.round(max(top_oil),0) == xfmr.T_tor + xfmr.T_ambr, str(method)
    
    if 'Bottom Liquid [C]' in xfmr.solution.keys():
        bot_oil = xfmr.solution['Bottom Liquid [C]']
        assert np.round(max(bot_oil),0) == xfmr.T_bor + xfmr.T_ambr, str(method)

def test_transformer_thermal_models():
    from .methods import AVAILABLE_METHODS
    for method in AVAILABLE_METHODS:
        execute_transformer_thermal_models(method)
    
if __name__ == "__main__":
    test_transformer_thermal_models()