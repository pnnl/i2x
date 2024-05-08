"""
This file contains tests for the hosting capacity time series functionality
"""

from i2x.der_hca import hca

if __name__ == "__main__":
    config = {"choice": "ieee9500",
              "res_pv_frac": 0,
              "solnmode": "YEARLY",
              "hca_method": "sequence",
              "numsteps": 1,
              "start_time": [0,0],
              "end_time": [5,0],
              "stepsize": 3600,
              "metrics": {
                    "include": {
                        "voltage": ["vmin", "vmax"],
                        "thermal": ["emerg", "norm_hrs"]      
                    },
                    "limits": {
                        "thermal": {"norm_hrs": 0} # no violations of normal limit allowed
                    },
                    "tolerances":{
                        "thermal":0.1
                    }
              },
              "monitors":
                {"volt_monitor_method": "none"},# don't add any additional voltage monitors
            } 
    # config["hca_log"] = {"loglevel": "debug"}
    h = hca.HCA(config, print_config=True)
    # h.runbase()
    h.logger.info("imported change lines:")
    h.logger.info(h.change_lines)

    h.runbase()
    h.hca_round("pv", recalculate=True, unset_active_bus=False)
    bus = h.active_bus
    h.step_solvetime()
    while not h.is_endtime():
        h.runbase(skipadditions=True)
        h.hca_round("pv", bus=bus, recalculate=True)
        h.step_solvetime()
    h.unset_active_bus()
    ## show the resulting hca for bus
    h.logger.info(f"Sequence HCA for bus {bus}")
    h.logger.info(h.get_hc("pv", bus))
    # for i in range(3):
    #     h.rundss(solvetime=h.solvetime)
    #     h.step_solvetime()

    # h.runbase()
    # h.hca_round("pv", recalculate=True) 

    ##TODO:
    ## If it's not possible to include inverter controls on anything other than pysystems and storage
    ## will need to add as pv system to allow for different inverter controls
    ## that means that the application of the curves will need to be more selective 
    ## than applying to all as is currently the case
    ## Alternatively we just assume that all inverters behave the same (unity power factor vs volt var etc.)