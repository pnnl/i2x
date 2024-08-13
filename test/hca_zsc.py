"""
This file contains tests for the hosting capacity time series functionality
"""

from i2x.der_hca import hca
import numpy as np
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="i2X Hosting Capacity Analysis")
    parser.add_argument("--bus", help="bus to conduct HCA (default: %(default)s)", default="n1134475")
    parser.add_argument("--start", type=int, help="starting hour (default: %(default)d)", default=0)
    parser.add_argument("--end", type=int, help="ending hour (default: %(default)d)", default=10)
    args = parser.parse_args()
    config = {"choice": "ieee9500",
              "res_pv_frac": 0,
              "pvcurve": "pclear",
              "solnmode": "YEARLY",
              "min_converged_vpu": 0.5, #if voltages below 0.5 treat as not converged
              "hca_method": "sequence",
              "change_lines_init": ["redirect hca_ts_IEEE9500prep.dss",
                                    ],
              "loadcurve": "loadshape4",
              "numsteps": 1, #only solve one snapshot at a time
              "start_time": [0,0],
              "end_time": [1,0],
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
                {"volt_monitor_method": "explicit",
                 "volt_monitor_list": [args.bus]},# don't add any additional voltage monitors
            } 
    config["hca_log"] = {"print_hca_iter": True}
    # config["hca_log"] = {"loglevel": "debug"}
    # config["debug_output"] = True
    # config["end_time"] = [1,0]
    h = hca.HCA(config, print_config=True)
    # h.runbase()
    h.logger.info("imported change lines:")
    h.logger.info(h.change_lines)
    
    ### First Timestep ###
    
    ### run the base needed for 2 reasons:
    ## 1: sets up base metrics for comparison
    ## 2: deactivation of regulator control happens here (TODO: maybe change this)
    h.runbase(skipadditions=False)

    ## activate bus
    h.dss.circuit.set_active_bus(args.bus)
    h.logger.info(f"Active bus is {h.dss.bus.name}")
    v0 = h.dss.bus.seq_voltages
    h.dss.bus.zsc_refresh # need this to recalculate array
    n = h.dss.bus.num_nodes
    zsc_r = [v for i,v in enumerate(h.dss.bus.zsc_matrix) if i % 2 == 0]
    zsc_i = [v for i,v in enumerate(h.dss.bus.zsc_matrix) if i % 2 == 1]
    zsc = np.reshape(zsc_r, (n,n)) + 1j*np.reshape(zsc_i, (n,n))

    ysc_r = [v for i,v in enumerate(h.dss.bus.ysc_matrix) if i % 2 == 0]
    ysc_i = [v for i,v in enumerate(h.dss.bus.ysc_matrix) if i % 2 == 1]
    ysc = np.reshape(ysc_r, (n,n)) + 1j*np.reshape(ysc_i, (n,n))

    h.logger.info("Testing Zsc * Ysc = I:")
    h.logger.info(f"{np.round(zsc.dot(ysc),6)}")

    a = np.exp(1j*np.pi*2/3)
    A = np.array([[1, 1, 1], [1, np.power(a,2), a], [1, a, np.power(a,2) ]])
    Ainv = (1/3)*np.array([[1, 1, 1], [1, a, np.power(a,2)], [1, np.power(a,2), a ]])

    zsc_seq = Ainv.dot(zsc[:3,:3]).dot(A)
    h.logger.info("Testing zsc1:")
    h.logger.info(f"\tzsc1 (DSS) = {complex(*h.dss.bus.zsc1):.6f}\tzsc1 (calc) = {zsc_seq[1,1]:.6f}\t{'Success' if np.abs(complex(*h.dss.bus.zsc1) - zsc_seq[1,1]) < 1e-6 else 'Failed'}")
    h.logger.info("Testing zsc0:")
    h.logger.info(f"\tzsc0 (DSS) = {complex(*h.dss.bus.zsc0):.6f}\tzsc1 (calc) = {zsc_seq[0,0]:.6f}\t{'Success' if np.abs(complex(*h.dss.bus.zsc0) - zsc_seq[0,0]) < 1e-6 else 'Failed'}")

    delta_kw = 0.03*np.power(h.dss.bus.kv_base*np.sqrt(3),2)/(h.dss.bus.zsc1[0]*h.inputs["invpf"] - h.dss.bus.zsc1[1]*np.sqrt(1 - h.inputs["invpf"]**2))*1000
    h.logger.info(f"\nDelta P (kw) leading to ~3% voltage change: {delta_kw:0.2f}")

    h.hca_round("pv", bus=args.bus, Sij={"kw": delta_kw, "kva": delta_kw/0.8},
                 recalculate=False, allow_violations=True, hciter=False)
    
    h.dss.circuit.set_active_bus(args.bus)
    h.logger.info(f"\nActive bus is {h.dss.bus.name}")
    v1 = h.dss.bus.seq_voltages
    h.logger.info(f"Voltage before is {v0[1]:0.1f} V ({v0[1]/1000/h.dss.bus.kv_base:0.3f} pu)")
    h.logger.info(f"Voltage after  is {v1[1]:0.1f} V ({v1[1]/1000/h.dss.bus.kv_base:0.3f} pu)")
    dv = 100*(v1[1] - v0[1])/1000/h.dss.bus.kv_base
    h.logger.info(f"Voltage change (w.r.t nominal voltage) due to addition of {delta_kw:0.2f} kW is {dv:0.2f}%")
