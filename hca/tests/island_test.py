import sys
import os
if os.path.abspath("..") not in sys.path:
    sys.path.append(os.path.abspath(".."))
import hca as h
import islands as isl
from hca_utils import Logger
import numpy as np
import pandas as pd
import PlotUtils as pu
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def sample_bus(hca, comps):
    buslist = [b for b in list(hca.graph_dirs["bus3phase"]) + hca.visited_buses if hca.G.nodes[b]["comp"] in comps if b not in hca.exauhsted_buses["pv"]]
    return hca.sample_buslist(buslist)

def main():
    ### load config (note: just changes to defaults)
    inputs = h.load_config("hca9500node_testconfig.json")
    inputs["invmode"] =  "CONSTANT_PF" #"VOLT_VAR_CATA"
    inputs["hca_log"]["logname"] = f'hca_island_test_{inputs["invmode"]}_comp1'
    inputs["hca_log"]["logtofilemode"] = "w"

    # disable line regulators but not substation regulators
    inputs["reg_control"]["disable_list"] = [f"vreg{i}_{j}" for i in [1,2,3] for j in ["a", "b", "c"]]

    # logger_heading = f"********* Run with {invmode} ****************"
    logger_heading = "*******************ISLAND TEST *******************"
    hca = h.HCA(inputs, logger_heading=logger_heading) # instantiate hca instance
    hca.runbase()       # run baseline

    n = 10
    while True:
        bus = sample_bus(hca, [1])
        hca.hca_round("pv", bus=bus)
        if "island_pq" in hca.metrics.last_violation_list:
            break
        elif hca.cnt > n:
            ### check if last n iterations produced no new capacity:
            kwsum = sum(hca.data["Stotal"][hca.cnt-i].loc["pv", "kw"] for i in range(n))
            if np.abs(kwsum - n*hca.data["Stotal"][hca.cnt].loc["pv", "kw"]) < 1e-4:
                hca.logger.info("\n----------------------\nUnable to find new locations. Stopping.")
                break
    hca.save(f'{inputs["hca_log"]["logname"]}.pkl')
    return
    ### redo the last step in a way that will trigger the thermal violations
    bus = hca.visited_buses[-1]
    hc, cnt = hca.get_hc("pv", bus)
    Sij, cnt = hca.get_data("Sij", "pv", bus, cnt=cnt)
    Sijnew = {"kw": hc["kw"] + Sij["kw"] + 50}
    Sijnew["kva"] = Sijnew["kw"]/0.8

    hca.logger.info("\n----------------------------\n")
    hca.logger.info(f"Resetting HCA round {cnt} for bus {bus}")
    hca.logger.info(f"Initial cap {Sij['kw']} | initial HC  {hc['kw']} | new cap {Sijnew['kw']}")
    hca.logger.info("\n----------------------------\n")
    
    hca.reset_dss()
    hca.cnt -= 1
    hca.hca_round("pv", bus=bus, Sij=Sijnew, allow_violations=True, hciter=True)

    hca.summary_outputs()
    if hca.metrics.violation_count > 0:
        h.print_config(hca.metrics.violation, title="Violations", printf=hca.logger.info)
        violations_list = hca.metrics.get_violation_list()
        if "voltage_vdiff" in violations_list:
            filenamebase = f"thermal_test_vdiff_{inputs['invmode']}_pre"
            pu.vdiff_plot(hca, filenamebase)
        if ("voltage_vmax" in violations_list) or ("voltage_vmin" in violations_list):
            filenamebase = f"thermal_test_vmaxmin_{inputs['invmode']}_pre"
            pu.vmaxmin_plot(hca, filenamebase)
        if "thermal_emerg" in violations_list:
            filenamebase = f"thermal_test_thermal_{inputs['invmode']}_pre"
            pu.thermal_plot(hca, filenamebase)
    else:
        h.print_config(hca.metrics.eval, title="Evaluation", printf=hca.logger.info)

    ## upagrade overloaded elements
    hca.logger.info("\n--------------------- Upgrading -------------------\n")
    hca.reset_dss()
    hca.cnt -= 1

    ## create upgrades
    for typ, names in hca.metrics.get_thermal_branches().items():
        for name in names:
            if typ.lower() == 'line':
                hca.upgrade_line(name)
            elif typ.lower() == "transformer":
                hca.upgrade_xfrm(name)
    h.print_config(hca.upgrades, title="Upgrades", printf=hca.logger.info)

    hca.hca_round("pv", bus=bus, Sij=Sijnew, allow_violations=True, hciter=True)

    hca.summary_outputs()
    if hca.metrics.violation_count > 0:
        h.print_config(hca.metrics.violation, title="Violations", printf=hca.logger.info)
        violations_list = hca.metrics.get_violation_list()
        if "voltage_vdiff" in violations_list:
            filenamebase = f"thermal_test_vdiff_{inputs['invmode']}_pre"
            pu.vdiff_plot(hca, filenamebase)
        if ("voltage_vmax" in violations_list) or ("voltage_vmin" in violations_list):
            filenamebase = f"thermal_test_vmaxmin_{inputs['invmode']}_pre"
            pu.vmaxmin_plot(hca, filenamebase)
        if "thermal_emerg" in violations_list:
            filenamebase = f"thermal_test_thermal_{inputs['invmode']}_pre"
            pu.thermal_plot(hca, filenamebase)
    else:
        h.print_config(hca.metrics.eval, title="Evaluation", printf=hca.logger.info)

if __name__ == "__main__":
    main()