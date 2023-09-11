import sys
import os
if os.path.abspath("..") not in sys.path:
    sys.path.append(os.path.abspath(".."))
import hca as h

def main(logname):
    ### load config (note: just changes to defaults)
    inputs = h.load_config("hca9500node_testconfig.json")
    inputs["invmode"] = "CONSTANT_PF"
    inputs["hca_log"]["logname"] = logname
    inputs["hca_log"]["logtofilemode"] = "w"

    # disable line regulators but not substation regulators
    inputs["reg_control"]["disable_list"] = [f"vreg{i}_{j}" for i in [1,2,3] for j in ["a", "b", "c"]]

    # logger_heading = f"********* Run with {invmode} ****************"
    logger_heading = "*******************HCA SAVE TEST *******************"
    hca = h.HCA(inputs, logger_heading=logger_heading) # instantiate hca instance
    hca.runbase()       # run baseline

    hca.hca_round("pv")

    hca.save("hca_save_tmp.pkl")

    hca.hca_round("pv")

    h.print_config(hca.data, printf=hca.logger.info, title="HCA DATA")

if __name__ == "__main__":
    
    main("hca_save_test1")

    reload_heading = "*******************RELOAD TEST *******************"
    hca = h.HCA("hca_save_tmp.pkl", reload=True, reload_filemode="a", logger_heading=reload_heading)
    hca.hca_round("pv")

    h.print_config(hca.data, printf=hca.logger.info, title="HCA DATA")