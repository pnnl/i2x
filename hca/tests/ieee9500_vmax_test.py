import sys
import os
if os.path.abspath("..") not in sys.path:
    sys.path.append(os.path.abspath(".."))
import hca as h
import islands as isl
from hca_utils import Logger


def main(vmax_array, invmode, logmode="a"):
    ### load config (note: just changes to defaults)
    inputs = h.load_config("hca9500node_testconfig.json")
    inputs["invmode"] = invmode
    inputs["hca_log"]["logname"] = "hca_vmax_test"
    inputs["hca_log"]["logtofilemode"] = logmode

    inputs["reg_control"] = False # disable regulator control to avoid vdiff issues

    logger_heading = f"********* Run with {invmode} ****************"
    hca = h.HCA(inputs, logger_heading=logger_heading) # instantiate hca instance
    hca.runbase()       # run baseline

    ### add solar to bus n1134480
    bus = "n1134480"
    Sij = {"kw": 3000}
    Sij["kva"] = Sij["kw"]/0.8
    hca.reset_dss()
    hca.hca_round("pv", bus=bus, Sij=Sij, allow_violations=True, hciter=False)

    vmax_array[invmode] = [hca.metrics.eval["voltage"]["vmax"]]
    hca.logger.info(f"(pre upgrade) vmax margin = {hca.metrics.eval['voltage']['vmax']}")

    if hca.metrics.violation_count == 0:
        vmax_array[invmode].append("No Upgrade")
    else:
        ## upgrade path
        H = hca.G.copy().to_undirected()
        ## get the open switches and remove them from the graph
        open_switches = isl.get_branch_elem(H, ['eclass', 'SwtOpen'], ['swtcontrol', True])
        H.remove_edges_from(open_switches)
        nearest_source, upgrade_path = isl.get_nearest_source(H, bus)

        ### upgrade path to nearest source by (double capacity, half impedance)
        upgrade_lines = []
        for u,v in zip(upgrade_path[:-1], upgrade_path[1:]):
            eclass = H.edges[u,v]["eclass"]
            ename = H.edges[u,v]["ename"]
            if H.edges[u,v]["eclass"] == "line":
                hca.dss.text(f"select {eclass}.{ename}")
                upgrade_lines.append(f"edit {eclass}.{ename} Length={hca.dss.lines.length/2:.7f} Normamps={hca.dss.lines.norm_amps*2:.2f} Emergamps={hca.dss.lines.emerg_amps*2:.2f}")
            elif H.edges[u,v]["eclass"] in ("regulator", "transformer"):
                # loop over any potential parallel transformers
                for xfrm in h.get_parallel_xfrm(hca.dss, ename):
                    h.activate_xfrm_byname(hca.dss, xfrm) #activate the transformer
                    #loop over windings and collect kva
                    kvas = []
                    for wdg in range(1, hca.dss.transformers.num_windings+1):
                        hca.dss.transformers.wdg = wdg # activate the winding
                        kvas.append(hca.dss.transformers.kva)
                    upgrade_lines.append(f"edit transformer.{xfrm} kvas=({', '.join(str(round(s*2)) for s in kvas)})")
        ### re-run with upgrades
        hca.reset_dss() # reset to before the last resource was added
        hca.replay_resource_addition("pv", bus, hca.cnt)
        hca.change_lines.extend(upgrade_lines)
        hca.logger.info("pre-run checks (change lines first -> resource and last -> upgrade transformer kva 2x")
        hca.logger.info(hca.logger.info(hca.change_lines[0]))
        hca.logger.info(hca.logger.info(hca.change_lines[-1]))
        hca.rundss() # run
        
        ### get metrics
        hca.metrics.load_res(hca.lastres)
        hca.metrics.calc_metrics()
        hca.logger.info(f"(post upgrade) vmax margin = {hca.metrics.eval['voltage']['vmax']}")
        vmax_array[invmode].append(hca.metrics.violation['voltage']['vmax'])

        hca.logger.info(f"\n********* Finished run with {invmode} **************")
        
    
if __name__ == "__main__":
    vmax_array = {}
    main(vmax_array, "CONSTANT_PF", logmode="w")
    
    ### Re-try with advanced inverter functions
    # 'VOLT_VAR_AVR'
    for invmode in ['VOLT_WATT', 'VOLT_VAR_CATA', 'VOLT_VAR_CATB', 'VOLT_VAR_VOLT_WATT', 'VOLT_VAR_14H']:
        main(vmax_array, invmode)

    hca_logger = Logger("hca_vmax_test", 
                         level="info", format="{message}")
    
    hca_logger.set_logfile(mode="a")
    hca_logger.info("\n**** Impact of Inverer Mode and Upgrade ****")
    for invmode, vmax in vmax_array.items():
        hca_logger.info(f"Results with inverter mode {invmode}")
        hca_logger.info(f"pre: {vmax[0]}, post: {vmax[1]}")
    