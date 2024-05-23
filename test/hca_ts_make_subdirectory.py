"""
This file contains tests for the hosting capacity time series functionality
"""

from i2x.der_hca import hca
import numpy as np
import os, sys

def add_subdir(subdir, param):
    return os.path.join(subdir, param)


if __name__ == "__main__":
    config = {"choice": "ieee9500",
              "res_pv_frac": 0,
              "pvcurve": "pclear",
              "solnmode": "YEARLY",
              "min_converged_vpu": 0.5, #if voltages below 0.5 treat as not converged
              "hca_method": "sequence",
              "change_lines_init": ["redirect hca_ts_IEEE9500prep.dss"],
              "loadcurve": "loadshape4",
              "numsteps": 1, #only solve one snapshot at a time
              "start_time": [0,0],
              "end_time": [10,0], #testing on just 5 iterations
              "stepsize": 3600,  #1 hr
              "reg_control": {
                    "disable_all": True, # disable all control, will be done via shape
                    "regulator_shape": { # regulator shape mapping
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
              },
              "storage_control": {
                  "storage_shape": { # map load objects representing storage to shape
                      "bat1": "bat1",
                      "bat2": "bat2"
                  }
              },
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
    config["hca_log"] = {"print_hca_iter": True, "logtofile": True}
    # config["hca_log"] = {"loglevel": "debug"}
    # config["debug_output"] = True
    # config["end_time"] = [1,0]
    
    ### create a subdirectory
    run_dir = "hca_in_subdirectory"
    cwd = os.getcwd() # save for later
    if not os.path.exists(run_dir):
        os.mkdir(run_dir)
    os.chdir(run_dir)

    ### prepend "up a step",i.e. .. to all paths in config
    for i, l in enumerate(config["change_lines_init"]):
        if "redirect" in l:
            path = l.split(" ")[1]
            config["change_lines_init"][i] = f"redirect {add_subdir('..', path)}"
    
    for k,v in config["reg_control"]["regulator_shape"].items():
        config["reg_control"]["regulator_shape"][k] = add_subdir("..", v)

    h = hca.HCA(config, print_config=True)
    # h.runbase()
    h.logger.info(f"current working directory: {os.getcwd()}")
    h.logger.info("imported change lines:")
    h.logger.info(h.change_lines)
    
    ### First Timestep ###
    
    ### run the base needed for 2 reasons:
    ## 1: sets up base metrics for comparison
    ## 2: deactivation of regulator control happens here (TODO: maybe change this)
    h.runbase(skipadditions=False)
        
    ### Perform HCA 
    # recalculate=True means no resource will actually be added --> important for multiple time periods
    # unset_active_bus=False means active bus will be kept so can be used in subsequent periods
    h.hca_round("pv", recalculate=True, unset_active_bus=False)
    bus = h.active_bus
    h.step_solvetime() # time step
    ### main loop ###
    while not h.is_endtime():
        ## base needs to be re-run for each time step
        # skipadditions=True means all the deterministic changes that are saved in history will not be applied twice
        h.runbase(skipadditions=True)

        ## seed the capacity with the last calculated HC
        Sij = {k: v for k,v in h.get_hc("pv", bus, latest=True)[0].items() if k in ["kw", "kva"]}
        if Sij["kw"] == 0:
            Sij = None
        
        ## calculate HCA specifying bus location and initial capacity
        h.hca_round("pv", bus=bus, Sij=Sij, recalculate=True,
                    bnd_strategy=("add", 500))#, set_sij_to_hc=True)
        h.step_solvetime()

    h.unset_active_bus()
    ## show the resulting hca for bus
    h.logger.info(f"Sequence HCA for bus {bus}")
    h.logger.info(h.get_hc("pv", bus))

    kw_res = np.array([5297.9062,5209.3060,4376.2749,4227.7636,
                       5042.6609,5030.4652,5029.2370,5028.0092,
                       5004.6859,4996.1330])
    
    err = np.linalg.norm(h.get_hc("pv", bus)["kw"].values - kw_res, np.inf)
    if err < 5: # current kw tolerance is hard coded as 5 kw
        h.logger.info(f"Success! (max error ({err:0.4f}) is within 5 kW)")
    else:
        h.logger.info(f"Failed! max error is {err:0.4f} > 5 kW")
    
    os.chdir(cwd)
    ##TODO:
    ## hca_control_mode and hca_control_pf are intended to allow different
    ## inverter behavior for the HCA resource compared to others.
    ## A) is this really desireable?
    ## B) if yes, this needs to be implemented (parameters are currently not used)