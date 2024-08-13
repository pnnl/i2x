
import time
from i2x.der_hca import hca
import numpy as np
import pandas as pd
from multiprocessing import Pool
import os, sys, shutil
import pickle
import argparse


class ParallHCA():
    def __init__(self, name:str):
        self.instances = []
        self.name = name
        self.logger = hca.Logger(name, format="{message}")
        self.logger.set_logfile(path=name)

    def update(self, h):
        tmp = pickle.loads(h)
        tmp["inputs"]["hca_log"]["logtofile"] = True
        tmp["inputs"]["hca_log"]["logtofilemode"] = "a"
        original_name = tmp["inputs"]["hca_log"]["logname"]
        tmp["inputs"]["hca_log"]["logname"] = self.name
        tmp["inputs"]["hca_log"]["logpath"] = self.name
        self.instances.append(hca.HCA(tmp, logger_heading=f"Reloading {original_name}",
                                      reload=True, reload_start_dss=False))
    def error(self, e):
        self.logger.error("Process failed to complete")
        sys.exit(1)

    def get_hca(self, bus) -> pd.DataFrame:
        return pd.concat([h.get_hc("pv", bus) for h in self.instances], axis=0).sort_index()


#def HCATEST(num1):
def parallel_hca(bus, num1, num2, logpath="..", savepath=".", return_full=False):
    #config = {"choice": "ieee9500{x}".format(x = num1),
    config = {"choice": "ieee9500",
                  "res_pv_frac": 0,
                  "pvcurve": "pclear",
                  "solnmode": "YEARLY",
                  "min_converged_vpu": 0.5,  # if voltages below 0.5 treat as not converged
                  "hca_method": "sequence",
                  "change_lines_init": ["redirect ../hca_ts_IEEE9500prep.dss"],
                  "loadcurve": "loadshape4",
                  "numsteps": 1,  # only solve one snapshot at a time
                  "start_time": [num1, 0],
                  "end_time": [num2, 0],  # testing on just 5 iterations
                  #"end_time": [num1+1, 0],  # testing on just 5 iterations
                  "stepsize": 3600,  # 1 hr
                  "reg_control": {
                      "disable_all": True,  # disable all control, will be done via shape
                      "regulator_shape": {  # regulator shape mapping
                          "vreg2_a": "../regulator_taps/hca9500node_Mon_vreg2_a_1wdg.csv",
                          "vreg2_b": "../regulator_taps/hca9500node_Mon_vreg2_b_1wdg.csv",
                          "vreg2_c": "../regulator_taps/hca9500node_Mon_vreg2_c_1wdg.csv",
                          "vreg3_a": "../regulator_taps/hca9500node_Mon_vreg3_a_1wdg.csv",
                          "vreg3_b": "../regulator_taps/hca9500node_Mon_vreg3_b_1wdg.csv",
                          "vreg3_c": "../regulator_taps/hca9500node_Mon_vreg3_c_1wdg.csv",
                          "vreg4_a": "../regulator_taps/hca9500node_Mon_vreg4_a_1wdg.csv",
                          "vreg4_b": "../regulator_taps/hca9500node_Mon_vreg4_b_1wdg.csv",
                          "vreg4_c": "../regulator_taps/hca9500node_Mon_vreg4_c_1wdg.csv",
                          "feeder_reg1a": "../regulator_taps/hca9500node_Mon_feeder_reg1a_1wdg.csv",
                          "feeder_reg1b": "../regulator_taps/hca9500node_Mon_feeder_reg1b_1wdg.csv",
                          "feeder_reg1c": "../regulator_taps/hca9500node_Mon_feeder_reg1c_1wdg.csv",
                          "feeder_reg2a": "../regulator_taps/hca9500node_Mon_feeder_reg2a_1wdg.csv",
                          "feeder_reg2b": "../regulator_taps/hca9500node_Mon_feeder_reg2b_1wdg.csv",
                          "feeder_reg2c": "../regulator_taps/hca9500node_Mon_feeder_reg2c_1wdg.csv",
                          "feeder_reg3a": "../regulator_taps/hca9500node_Mon_feeder_reg3a_1wdg.csv",
                          "feeder_reg3b": "../regulator_taps/hca9500node_Mon_feeder_reg3b_1wdg.csv",
                          "feeder_reg3c": "../regulator_taps/hca9500node_Mon_feeder_reg3c_1wdg.csv",
                      }
                  },
                  "storage_control": {
                      "storage_shape": {  # map load objects representing storage to shape
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
                          "thermal": {"norm_hrs": 0}  # no violations of normal limit allowed
                      },
                      "tolerances": {
                          "thermal": 0.1
                      }
                  },
                  "monitors":
                      {"volt_monitor_method": "none"},  # don't add any additional voltage monitors
                  }

    #config["hca_log"] = {"print_hca_iter": True}
    config["hca_log"] = {"print_hca_iter": True, "logtofile": True, 
                         "logpath": logpath, "logname": "hcalog{x}-{y}".format(x = num1, y=num2)}
    #config["hca_log"] = {"loglevel": "debug"}
    #config["debug_output"] = True

    ### create a subdirectory
    run_dir = "hca{x}-{y}".format(x = num1, y= num2)
    cwd = os.getcwd()  # save for later
    if not os.path.exists(run_dir):
        os.mkdir(run_dir)
    os.chdir(run_dir)

    h = hca.HCA(config, print_config=True)
    h.cnt = h.solvetime[0] #set count to be hours of year
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
    h.hca_round("pv", bus=bus, recalculate=True)
    
    h.step_solvetime()  # time step
    ### main loop ###
    while not h.is_endtime():
        ## base needs to be re-run for each time step
        # skipadditions=True means all the deterministic changes that are saved in history will not be applied twice
        h.runbase(skipadditions=True)

        ## seed the capacity with the last calculated HC
        Sij = {k: v for k, v in h.get_hc("pv", bus, latest=True)[0].items() if k in ["kw", "kva"]}
        if Sij["kw"] == 0:
            Sij = None

        ## calculate HCA specifying bus location and initial capacity
        h.hca_round("pv", bus=bus, Sij=Sij, recalculate=True,
                        bnd_strategy=("add", 100))  # , set_sij_to_hc=True)
        h.step_solvetime()

    h.unset_active_bus()
    ## show the resulting hca for bus
    h.logger.info(f"Sequence HCA for bus {bus}")
    h.logger.info(h.get_hc("pv", bus))

    os.chdir(cwd)
    ## save the results
    h.save(os.path.join(savepath,f"hca{num1}-{num2}.pkl"))
    ## delete the temporary folder
    shutil.rmtree(run_dir)
    if return_full:
        return h
    else:
        return h.save(None)


if __name__ == "__main__":
    # buses = ['regxfmr_hvmv11sub1_lsb', 'm1009705', 'm1047507', 'l2925506', 'm1027039']
    buses = ['regxfmr_hvmv11sub1_lsb']
    nprocess = 8
    hrs = 8760
    hrs_per_process = np.round(hrs/nprocess)
    
    ## this is a SERIES (NOT PARALLEL) loop over the buses to calculate HCA on
    for bus in buses:
        ## Results output folder
        dirname = f"hca_{bus}"
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        
        ## create parallel HCA container
        ph = ParallHCA(dirname)        

        ph.logger.info(f"Running parallel HCA at bus {bus}")
        ph.logger.info(f"\t{nprocess} parallel process for {hrs} ==> {hrs_per_process} per process")
        ### parallel processing
        timer = hca.ProcessTime()
        timer.start()
        pool = Pool(nprocess)

        ## parallel loop to solve all hrs of HCA
        for p in range(nprocess):
            num1 = int(hrs_per_process*p)
            num2 = hrs if p == (nprocess-1) else min(int(hrs_per_process*(p+1)), hrs)
            if num1 >= hrs:
                # edge case: no more hours to calcualte
                continue
            args = (bus, num1, num2)
            kwargs = {"logpath": f"../{dirname}", "savepath": dirname}
            ph.logger.info(f"Process {p} has inputs {args}")
            ph.logger.info(f"\targs\t{args}")
            ph.logger.info(f"\tkwargs\t{kwargs}")
            pool.apply_async(parallel_hca, args=args, kwds=kwargs, callback=ph.update, error_callback=ph.error)
        pool.close()
        pool.join()

        ph.logger.info(f'Elapsed Time (s): {timer.stop(print=True)}')
        
        # Save result to csv
        ph.get_hca(bus).to_csv(os.path.join(dirname, "hca_result.csv"))

        pool.terminate()
        pool.close()
