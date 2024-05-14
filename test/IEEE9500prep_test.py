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

def monitor2df(dss:hca.py_dss_interface.DSS, monitorname) -> pd.DataFrame:
    """export monitor values to a dataframe"""
    idx = hca.activate_monitor_byname(dss, monitorname)
    if idx == 0:
        raise NameError(f"Monitor {monitorname} not found")
    return pd.DataFrame({k: dss.monitors.channel(i+1) for i,k in enumerate(dss.monitors.header)})

def compare_snap(v1:np.array, v2:np.array, tol=1e-3):
    """compare 2 arrays for a maximum error tolerance less than tol"""
    err = np.linalg.norm(v1-v2, np.inf)
    return err < tol, err

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
        t, err = test_monitor(h.dss, f"vreg{i}a", f"regulator_taps/hca9500node_Mon_vreg{i}_a_1wdg.csv", "tap_pu",
                              config["start_time"][0], tol=0.2/32/2, channel=1)
        h.logger.info(f"Regulator test for vreg{i}a {'passed' if t else f'failed {err:0.6f}'}.")
    for i in [1,2,3]:
        t, err = test_monitor(h.dss, f"feeder_reg{i}a", f"regulator_taps/hca9500node_Mon_feeder_reg{i}a_1wdg.csv","tap_pu",
                              config["start_time"][0], tol=0.2/32/2, channel=1)
        h.logger.info(f"Regulator test for feeder_reg{i}a {'passed' if t else f'failed {err:0.6f}'}.")
    
    ## test batteries
    for i in [1,2]:
        t, err = test_monitor(h.dss, f"bat{i}",f"batt_setting/hca9500node_Mon_battmeter{i}_1.csv", "p1(kw)",
                              config["start_time"][0], tol=0.1, channel=1, sign=-1)
        h.logger.info(f"Battery {i} test {'passed' if t else f'failed {err:0.6f}'}.")

    volt_save = h.lastres["di_voltexceptions"].copy()
    battery = {f"bat{i}": monitor2df(h.dss, f"bat{i}") for i in [1,2]}
    vreg = {f"vreg{i}a": monitor2df(h.dss, f"vreg{i}a") for i in [2,3,4]}
    feeder_reg = {f"feeder_reg{i}a": monitor2df(h.dss, f"feeder_reg{i}a") for i in [1,2,3]}

    # if False:
    #######################
    # alter configuration
    #######################
    config["numsteps"] = 1 # solving just one step at a time
    # point to different prep file: batteries replaced with load
    config["change_lines_init"] = ["redirect hca_ts_IEEE9500prep_test.dss"]
    config["reg_control"] = {
        "disable_all": True, # disable all control, will be done via shape
        "regulator_shape": {
            "vreg2_a": "regulator_taps/hca9500node_Mon_vreg2_a_1wdg.csv",
            "vreg2_b": "regulator_taps/hca9500node_Mon_vreg2_b_1wdg.csv",
            "vreg2_c": "regulator_taps/hca9500node_Mon_vreg2_c_1wdg.csv",
            "vreg3_a": "regulator_taps/hca9500node_Mon_vreg3_a_1wdg.csv",
            "vreg3_b": "regulator_taps/hca9500node_Mon_vreg3_b_1wdg.csv",
            "vreg3_c": "regulator_taps/hca9500node_Mon_vreg3_c_1wdg.csv",
            "vreg4_a": "regulator_taps/hca9500node_Mon_vreg4_a_1wdg.csv",
            "vreg4_b": "regulator_taps/hca9500node_Mon_vreg4_b_1wdg.csv",
            "vreg4_c": "regulator_taps/hca9500node_Mon_vreg4_c_1wdg.csv",
            "feeder_reg1a": "regulator_taps/hca9500node_Mon_feeder_reg1a_1wdg.csv",
            "feeder_reg1b": "regulator_taps/hca9500node_Mon_feeder_reg1b_1wdg.csv",
            "feeder_reg1c": "regulator_taps/hca9500node_Mon_feeder_reg1c_1wdg.csv",
            "feeder_reg2a": "regulator_taps/hca9500node_Mon_feeder_reg2a_1wdg.csv",
            "feeder_reg2b": "regulator_taps/hca9500node_Mon_feeder_reg2b_1wdg.csv",
            "feeder_reg2c": "regulator_taps/hca9500node_Mon_feeder_reg2c_1wdg.csv",
            "feeder_reg3a": "regulator_taps/hca9500node_Mon_feeder_reg3a_1wdg.csv",
            "feeder_reg3b": "regulator_taps/hca9500node_Mon_feeder_reg3b_1wdg.csv",
            "feeder_reg3c": "regulator_taps/hca9500node_Mon_feeder_reg3c_1wdg.csv",
        }
    }
    config["storage_control"] = {
        "storage_shape": {
            "bat1": "bat1",
            "bat2": "bat2"
        }
    }
    
    tstart = 0
    config["start_time"] = [tstart,0] # specify a start time not of 0 to test capability
    config["end_time"] = [10,0] # specify an endtime
    h = hca.HCA(config, logger_heading="\nretrying one at a time\n")
    while not h.is_endtime():
        h.logger.info(f"\nSolve time is: {h.solvetime}")
        h.runbase(skipadditions=h.solvetime[0]!=tstart)
        for v in ["bat1", "bat2"]:
            t, err = compare_snap(-1*battery[v].loc[h.solvetime[0]].iloc[[0,1]].values, monitor2df(h.dss, v).values)
            h.logger.info(f"Battery {v} test {'passed' if t else f'failed {err:0.6f}'}.")
        for v in vreg.keys():
            t = vreg[v].loc[h.solvetime[0]].iloc[0] == monitor2df(h.dss, v).iloc[0,0]
            h.logger.info(f"Regulator test for {v} {'passed' if t else f'failed {vreg[v].iloc[h.solvetime[0], 0]:0.5f} (ts) != {monitor2df(h.dss, v).iloc[0,0]:0.5f} (snap)'}.")
        for v in feeder_reg.keys():
            t = feeder_reg[v].loc[h.solvetime[0]].iloc[0] == monitor2df(h.dss, v).iloc[0,0]
            h.logger.info(f"Regulator test for {v} {'passed' if t else f'failed {feeder_reg[v].iloc[h.solvetime[0], 0]:0.5f} (ts) != {monitor2df(h.dss, v).iloc[0,0]:0.5} (snap)'}.")
        ## test voltage limits
        t, err = compare_snap(h.lastres["di_voltexceptions"].select_dtypes("number").squeeze().values, 
                    volt_save.select_dtypes("number").loc[h.solvetime[0]+1].values,
                    tol=.01)
        h.logger.info(f"Voltage limits test {'passed' if t else f'failed {err:0.5f}'}")
        h.step_solvetime()
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


    