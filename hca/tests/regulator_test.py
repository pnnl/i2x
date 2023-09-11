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


def main(invmode):
    ### load config (note: just changes to defaults)
    inputs = h.load_config("hca9500node_testconfig.json")
    inputs["invmode"] = invmode #'VOLT_VAR_CATA' #"CONSTANT_PF"
    inputs["hca_log"]["logname"] = f'hca_regulator_test_{inputs["invmode"]}'
    inputs["hca_log"]["logtofilemode"] = "w"

    # disable line regulators but not substation regulators
    inputs["reg_control"]["disable_list"] = [f"vreg{i}_{j}" for i in [1,2,3] for j in ["a", "b", "c"]]

    # logger_heading = f"********* Run with {invmode} ****************"
    logger_heading = "*******************REGULATOR TEST *******************"
    hca = h.HCA(inputs, logger_heading=logger_heading) # instantiate hca instance
    hca.runbase()       # run baseline

    ### add solar to bus n1134480
    bus = "n1134480"
    # Sij = {"kw": 3250}
    Sij = {"kw": 4100}
    Sij["kva"] = Sij["kw"]/0.8
    hca.reset_dss()
    hca.hca_round("pv", bus=bus, Sij=Sij, allow_violations=True, hciter=True)

    hca.summary_outputs()
    if hca.metrics.violation_count > 0:
        h.print_config(hca.metrics.violation, title="Violations", printf=hca.logger.info)
        violations_list = hca.metrics.get_violation_list()
        if "voltage_vdiff" in violations_list:
            filenamebase = f"regulator_test_vdiff_{inputs['invmode']}_pre"
            pu.vdiff_plot(hca, filenamebase)
        elif ("voltage_vmax" in violations_list) or ("voltage_vmin" in violations_list):
            filenamebase = f"regulator_test_vmaxmin_{inputs['invmode']}_pre"
            pu.vmaxmin_plot(hca, filenamebase)
    else:
        h.print_config(hca.metrics.eval, title="Evaluation", printf=hca.logger.info)
    
    # vdiff_locations = hca.metrics.get_vdiff_locations()
    # fig = make_subplots(2, 1, shared_xaxes=True, subplot_titles=("node voltage", "node voltage diff"))
    # colors = pu.ColorList()
    # for node in vdiff_locations["v"].keys():
    #     x2 = list(range(len(vdiff_locations["vdiff"][node])))
    #     x1 = list(range(len(vdiff_locations["v"][node])))
    #     pu.add_trace(fig, x1, vdiff_locations["v"][node], f"{node}_v", colors=colors, row=1)
    #     pu.add_trace(fig, x2, vdiff_locations["vdiff"][node], f"{node}_dv", colors=colors, row=2)
    #     colors.step()
    # fig.update_yaxes(title_text="V [p.u.]", row=1, col=1)
    # fig.update_yaxes(title_text="dV [%]", row=2, col=1)
    # fig.write_html(f"regulator_test_vdiff_{inputs['invmode']}_pre.html")
    # hca.plot(highlight_nodes=list(vdiff_locations["v"].keys()), pdf_name=f"regulator_test_vdiff_{inputs['invmode']}_pre.pdf", on_canvas=True)
    
    # hca.logger.info(f"(pre upgrade) vmax margin = \n\t{hca.metrics.eval['voltage']['vmax']}")

    ## change regulator setpoint
    H = hca.G.copy().to_undirected()
    ## get the open switches and remove them from the graph
    open_switches = isl.get_branch_elem(H, ['eclass', 'SwtOpen'], ['swtcontrol', True])
    H.remove_edges_from(open_switches)
    nearest_source, upgrade_path = isl.get_nearest_source(H, bus)

    ## get the substation regulator:
    for u,v in zip(reversed(upgrade_path[:-1]), reversed(upgrade_path[1:])):
        eclass = H.edges[u,v]["eclass"]
        ename = H.edges[u,v]["ename"]
        if H.edges[u,v]["eclass"] == "regulator":
            break
    hca.logger.info(f"Found substation regulator {ename}")
    
    ## Increase vreg for the substation transformer until
    ## no violation or maximum reached
    while True:
        reg_changelines = []
        for xfrm in h.get_parallel_xfrm(hca.dss, ename):
            h.activate_xfrm_byname(hca.dss, xfrm) # activate the transformer
            err = h.get_regcontrol(hca.dss, xfrm) # activate the control
            if err <= 0:
                raise ValueError(f"Didn't find a controler for {xfrm}")
            # activate transformer winding controled by the regulator
            hca.dss.transformers.wdg = hca.dss.regcontrols.winding
            vbase = (1000*hca.dss.transformers.kv)
            pt = hca.dss.regcontrols.pt_ratio
            vreg_min = np.floor(1.0*vbase/pt)
            vreg_max = np.ceil(1.045*vbase/pt)
            vreg = hca.dss.regcontrols.forward_vreg
            vreg_pu = vreg*pt/vbase
            # vreg_pu_new = (1 + vreg_pu)/2
            # vreg_new = min(round(vreg_pu_new*vbase/pt), vreg-1)
            # vreg_new = max(vreg_new, vreg_min)
            vreg_new = min(vreg+1, vreg_max)
            reg_changelines.append(f"edit regcontrol.{hca.dss.regcontrols.name} vreg={vreg_new}")

        hca.reset_dss()
        hca.cnt -= 1
        hca.change_lines.extend(reg_changelines)
        for l in hca.change_lines:
            hca.logger.info(l)
        hca.hca_round("pv", bus=bus, Sij=Sij, allow_violations=True, hciter=True)

        if (hca.metrics.violation_count == 0) or vreg_new == vreg_max:
            break
        else:
            hca.logger.info("\nRe-iterating on vreg\n")

    hca.summary_outputs()
    if hca.metrics.violation_count > 0:
        h.print_config(hca.metrics.violation, title="Violations", printf=hca.logger.info)
        violations_list = hca.metrics.get_violation_list()
        if "voltage_vdiff" in violations_list:
            filenamebase = f"regulator_test_vdiff_{inputs['invmode']}_post"
            pu.vdiff_plot(hca, filenamebase)
        elif ("voltage_vmax" in violations_list) or ("voltage_vmin" in violations_list):
            filenamebase = f"regulator_test_vmaxmin_{inputs['invmode']}_post"
            pu.vmaxmin_plot(hca, filenamebase)
    else:
        h.print_config(hca.metrics.eval, title="Evaluation", printf=hca.logger.info)

if __name__ == "__main__":
    for invmode in ['VOLT_VAR_CATA', "CONSTANT_PF"]:
        main(invmode)
    