"""
This file contains tests for the hosting capacity time series functionality
"""
import py_dss_interface
import numpy as np
import pandas as pd
from i2x.der_hca import hca, PlotUtils as pltutil
import i2x.der_hca.islands as isl
import networkx as nx


def bfs_buses(h:hca.HCA, ntotal:int=5, depth_step=None,
              viable_buses:list=None) -> list:
    """
    Select ntotal buses to run hca at varying depth from the feeder source
    """
    
    if viable_buses is None:
        # use only buses that are three phase 12.47 kV
        viable_buses = [k for k,v in h.graph_dirs["all3phase"].items() if v["kv"] == 12.47]

    
    H = isl.get_nondir_tree(h.G)
    source = isl.get_single_source(H)
    diam = nx.eccentricity(H, v=source)
    if depth_step is None:
        depth_step = round(diam/ntotal)
    out = []
    depth = 1
    while depth <= diam:
        n = nx.descendants_at_distance(H, source, depth) # n is a set
        n = list(n.intersection(viable_buses)) #
        if n:
            n.sort() # for reproducibility
            # sample list using hca object random state for reproducibility
            out.append(n[h.random_state.randint(0, len(n))])
            depth += depth_step
        else:
            depth += 1
    if len(out) < ntotal:
        return bfs_buses(h, ntotal=ntotal, depth_step=depth_step-1, viable_buses=viable_buses)
    else:
        return out

if __name__ == "__main__":
    config = {"choice": "ieee9500",
            #   "res_pv_frac": 0,
            #   "pvcurve": "pclear",
            #   "solnmode": "YEARLY",
            #   "change_lines_init": ["redirect IEEE9500prep_test.dss"],#, "batchedit regcontrol..* maxtapchange=33"],
            #   "loadcurve": "loadshape4",
            #   "hca_method": "sequence",
            #   "allow_forms": 1,
            #   "numsteps": 48, #just testing solution
            #   "start_time": [0,0],
            #   "stepsize": 3600,
            #   "metrics": {
            #         "include": {
            #             "voltage": ["vmin", "vmax"],
            #             "thermal": ["emerg", "norm_hrs"]      
            #         },
            #         "limits": {
            #             "thermal": {"norm_hrs": 0} # no violations of normal limit allowed
            #         },
            #         "tolerances":{
            #             "thermal":0.1
            #         }
            #   },
            #   "monitors":
            #     {"volt_monitor_method": "none"},# don't add any additional voltage monitors
            } 
    # config["hca_log"] = {"loglevel": "debug"}
    h = hca.HCA(config)
    hca_buses = bfs_buses(h)
    h.logger.info("selected buses:")
    h.logger.info(hca_buses)
    # plot the selected nodes
    feeder_plotter=pltutil.PlotlyFeeder()
    feeder_plotter.plot(h.G, "IEEE9500_selected_hca_buses.html", highlight_nodes={k: "" for k in hca_buses})


    