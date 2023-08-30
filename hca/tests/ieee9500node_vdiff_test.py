import sys
import os
if os.path.abspath("..") not in sys.path:
    sys.path.append(os.path.abspath(".."))
import hca as h
import islands as isl
import pandas as pd
import networkx as nx

def main(vdiff_array, invmode, logmode="a"):
    ### load config (note: just changes to defaults)
    inputs = h.load_config("hca9500node_testconfig.json")
    inputs["invmode"] = invmode
    inputs["hca_log"]["logname"] = "hca_vdiff_test"
    inputs["hca_log"]["logtofilemode"] = logmode

    hca = h.HCA(inputs) # instantiate hca instance
    hca.logger.info(f"********* Run with {invmode} ****************")
    hca.runbase()       # run baseline

    ### add solar to bus n1134480
    bus = "n1134480"
    Sij = {"kw": 450}
    Sij["kva"] = Sij["kw"]/0.8
    # run hca round allowing violations (violation should occur)
    hca.hca_round("pv", bus=bus, Sij=Sij, allow_violations=True)

    vdiff_array[invmode] = [hca.metrics.violation['voltage']['vdiff']]
    hca.logger.info(f"(post addition) vdiff margin = {hca.metrics.violation['voltage']['vdiff']}")

    ###### Upgrade path 
    # get the last der added: last bus visited (we append), first shunt in list (we pre-pend)
    last_bus = hca.visited_buses[-1]
    last_der = hca.G.nodes[hca.visited_buses[-1]]["ndata"]["shunts"][0]
    hca.logger.info(f"last bus: {last_bus}, last_der: {last_der}")

    # get path to source
    H = hca.G.copy().to_undirected()
    ## get the open switches and remove them from the graph
    open_switches = isl.get_branch_elem(H, ['eclass', 'SwtOpen'], ['swtcontrol', True])
    H.remove_edges_from(open_switches)
    print("H connected components ", nx.number_connected_components(H))

    #path to upgrade
    upgrade_path = nx.shortest_path(H, last_bus, "sourcebus") 

    # upgrade all lines between resource and source
    upgrade_lines = []
    for u,v in zip(upgrade_path[:-1], upgrade_path[1:]):
        eclass = H.edges[u,v]["eclass"]
        ename = H.edges[u,v]["ename"]
        if H.edges[u,v]["eclass"] == "line":
            hca.dss.text(f"select {eclass}.{ename}") #activate line
            # halve the length, double the rating (intended to simulate a parallel line)
            upgrade_lines.append(f"edit {eclass}.{ename} Length={hca.dss.lines.length/2:.7f} Normamps={hca.dss.lines.norm_amps*2:.2f} Emergamps={hca.dss.lines.emerg_amps*2:.2f}")
        elif H.edges[u,v]["eclass"] in ("regulator", "transformer"):
            # loop over any potential parallel transformers (if single legs modeled)
            for xfrm in h.get_parallel_xfrm(hca.dss, ename):
                h.activate_xfrm_byname(hca.dss, xfrm) #activate the transformer
                #loop over windings and collect kva
                kvas = []
                for wdg in range(1, hca.dss.transformers.num_windings+1):
                    hca.dss.transformers.wdg = wdg # activate the winding
                    kvas.append(hca.dss.transformers.kva)
                # double the rating to also reduce the impedance 
                upgrade_lines.append(f"edit transformer.{xfrm} kvas=({', '.join(str(round(s*2)) for s in kvas)})")

    ### Re-Run
    hca.reset_dss() # reset to before the last resource was added
    hca.replay_resource_addition("pv", last_bus, hca.cnt) #re-add the pv resource
    hca.change_lines.extend(upgrade_lines) # add all the upgrades
    ### print first change line to verify resource is being 
    #print last line to verify upgrades are happening
    hca.logger.info("pre-run checks (change lines first -> resource and last -> upgrade 75000 kva 2x")
    hca.logger.info(hca.logger.info(hca.change_lines[0]))
    hca.logger.info(hca.logger.info(hca.change_lines[-1]))
    # for l in hca.change_lines:
    #     hca.logger.info(l)
    hca.rundss() # run
    # get metrics
    hca.metrics.load_res(hca.lastres)
    hca.metrics.calc_metrics()
    hca.logger.info(f"(post upgrade) vdiff margin = {hca.metrics.violation['voltage']['vdiff']}")
    vdiff_array[invmode].append(hca.metrics.violation['voltage']['vdiff'])

    hca.logger.info(f"\n********* Finished run with {invmode} **************")
    return hca

if __name__ == "__main__":
    vdiff_array = {}
    hca = main(vdiff_array, "CONSTANT_PF", logmode="w")
    ### Re-try with advanced inverter functions
    for invmode in ['VOLT_WATT', 'VOLT_VAR_CATA', 'VOLT_VAR_CATB', 'VOLT_VAR_AVR', 'VOLT_VAR_VOLT_WATT', 'VOLT_VAR_14H']:
        hca = main(vdiff_array, invmode)

    hca.logger.info("\n**** Impact of Inverer Mode and Upgrade ****")
    for invmode, vdiff in vdiff_array.items():
        hca.logger.info(f"Results with inverter mode {invmode}")
        hca.logger.info(f"pre: {vdiff[0]}, post: {vdiff[1]}")
    

