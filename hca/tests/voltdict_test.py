"""
THis tests is intended to verify that tha random number state works as expected.
Since it is seeded, the "randomness" should be repeatable and the voltage monitors
should be identical in multiple runs. 

It is recommended to do run this twice and compare the output of two separate runs.
For example, it was found the the set() may be repeated the same way on in the two
consecutive runs but not between two invocations of this test.
"""
import sys
import os
if os.path.abspath("..") not in sys.path:
    sys.path.append(os.path.abspath(".."))
import hca as h
import islands as isl
from hca_utils import Logger

def main(logname, logmode="w"):
    ### load config (note: just changes to defaults)
    inputs = h.load_config("hca9500node_testconfig.json")
    inputs["invmode"] = "CONSTANT_PF"
    
    inputs["hca_log"]["logname"] = logname
    inputs["hca_log"]["logtofilemode"] = logmode

    # disable line regulators but not substation regulators
    inputs["reg_control"]["disable_list"] = [f"vreg{i}_{j}" for i in [1,2,3] for j in ["a", "b", "c"]]

    # logger_heading = f"********* Run with {invmode} ****************"
    logger_heading = "*******************VOLTDICT TEST *******************"
    hca = h.HCA(inputs, logger_heading=logger_heading) # instantiate hca instance
    return [s.split("monitor.")[1].split(" ")[0].split("_")[0] for s in hca.change_lines_noprint]

if __name__ == "__main__":
    
    i = 1
    while True:
        logname = f"hca_voltdict_test{i}"
        if not os.path.isfile(logname+".log"):
            break
        i += 1
    
    vdict1 = main(logname, logmode="w")
    vdict2 = main(logname, logmode="a")

    
    hca_logger = Logger(logname, 
                         level="info", format="{message}")
    hca_logger.set_logfile(mode="a")
    hca_logger.info("\n*******Comparison of 2 voltdicts***********")
    if vdict1 == vdict2:
        hca_logger.info("Both volt dicts are identical")
    else:
        hca_logger.info("The two voltdicts are not identical:")
    hca_logger.info("vdict1   \t\t\t   vdict2\n------------------------------")
    for i in range(max(len(vdict1), len(vdict2))):
        try:
            s = f"{vdict1[i]}\t\t\t   "
        except IndexError:
            s = "         \t\t\t   "
        try:
            s += f"{vdict2[i]}"
        except IndexError:
            s += "   "
        hca_logger.info(s)
            