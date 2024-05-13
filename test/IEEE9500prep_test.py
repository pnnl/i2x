"""
This file contains tests for the hosting capacity time series functionality
"""
import py_dss_interface
import numpy as np
import pandas as pd
from i2x.der_hca import hca

def test_monitor(dss:hca.py_dss_interface.DSS, monitorname, filename, filecol, ninit, 
                 tol=0.2/32/2, channel=1, sign=1):
    """test monitor values agains a file"""

    idx = hca.activate_monitor_byname(dss, monitorname)
    if idx == 0:
        raise NameError(f"Monitor {monitorname} not found")
    monitor_value = np.array(dss.monitors.channel(channel))*sign
    numsteps = monitor_value.shape[0]
    df = pd.read_csv(filename).rename(columns=lambda x: x.lower().replace('"','').replace(' ',''))
    err = np.linalg.norm(monitor_value - df[filecol].iloc[ninit:(numsteps+ninit)].values, np.inf)
    return  err < tol, err


if __name__ == "__main__":
    config = {"choice": "ieee9500",
              "res_pv_frac": 0,
              "pvcurve": "pclear",
              "solnmode": "YEARLY",
              "change_lines_init": ["redirect IEEE9500prep_test.dss"],#, "batchedit regcontrol..* maxtapchange=33"],
              "loadcurve": "loadshape4",
              "hca_method": "sequence",
              "allow_forms": 1,
              "numsteps": 48, #just testing solution
              "start_time": [0,0],
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
    h.logger.info(h.lastres["di_voltexceptions"])
    
    ## test regulators
    for i in [2,3,4]:
        t, err = test_monitor(h.dss, f"vreg{i}a", f"regulator_taps/hca9500node_Mon_vreg{i}_a_1.csv", "tap(pu)",
                              config["start_time"][0], tol=0.2/32/2, channel=1)
        h.logger.info(f"Regulator test for vreg{i}a {'passed' if t else f'failed {err:0.6f}'}.")
    for i in [1,2,3]:
        t, err = test_monitor(h.dss, f"feeder_reg{i}a", f"regulator_taps/hca9500node_Mon_feeder_reg{i}a_1.csv","tap(pu)",
                              config["start_time"][0], tol=0.2/32/2, channel=1)
        h.logger.info(f"Regulator test for feeder_reg{i}a {'passed' if t else f'failed {err:0.6f}'}.")
    
    ## test batteries
    for i in [1,2]:
        t, err = test_monitor(h.dss, f"bat{i}",f"batt_setting/hca9500node_Mon_battmeter{i}_1.csv", "p1(kw)",
                              config["start_time"][0], tol=0.1, channel=1, sign=-1)
        h.logger.info(f"Battery {i} test {'passed' if t else f'failed {err:0.6f}'}.")

    volt_save = h.lastres["di_voltexceptions"].copy()
    if False:
        ## trying one at a time
        ## to go one at a time we need to:
            ## fix the taps to the right setting
            ## update the battery state of charge appropriately so it continues to follow its shape correctly.
        h.logger.info("\nretrying one at a time\n")
        config["numsteps"] = 1
        for t in range(3):
            config["start_time"] = [t, 0]
            h = hca.HCA(config, logger_heading=f"dss time {t} hr")
            h.rundss()
            h.logger.info(h.lastres["di_voltexceptions"])

    ## look at things like the battery, generator, loadshape
    # h.dss.text("Plot monitor object=bat1 channel=[1,2]") # Battery output
    # h.dss.text("Plot monitor object=bat1 channel=[4]") # Battery state of charge
    # h.dss.text("Plot monitor object=steamgen1_gen_pq channel=[1,2]") # generator output
    # h.dss.text("Plot loadshape Object=LoadShape4") # load shape
    # h.dss.text("Plot monitor object=vreg2a channel=[1]") # regulator taps


    