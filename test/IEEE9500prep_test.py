"""
This file contains tests for the hosting capacity time series functionality
"""

from i2x.der_hca import hca

if __name__ == "__main__":
    config = {"choice": "ieee9500",
              "res_pv_frac": 0,
              "solnmode": "YEARLY",
              "change_lines_init": ["redirect IEEE9500prep.dss"],
              "hca_method": "sequence",
              "allow_forms": 1,
              "numsteps": 48, #just testing solution
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
    h.rundss()

    ## look at things like the battery, generator, loadshape
    h.dss.text("Plot monitor object=bat1 channel=[1,2]") # Battery output
    h.dss.text("Plot monitor object=bat1 channel=[1,2,4]") # Battery state of charge
    h.dss.text("Plot monitor object=steamgen1_gen_pq channel=[1,2]") # generator output
    h.dss.text("Plot loadshape Object=LoadShape4") # load shape
    h.dss.text("Plot monitor object=vreg2a channel=[1]") # regulator taps


    