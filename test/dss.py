import py_dss_interface
dss = py_dss_interface.DSSDLL()

dss.text('compile c:/src/i2x/src/i2x/models/ieee_lvn/secpar.dss')
dss.text('show voltages')

