# IEEE Low-Voltage Network Model for i2x

This repository contains OpenDSS files for the IEEE North American Low Voltage Test circuit.

* See [CIMHub](https://github.com/GRIDAPPSD/CIMHub/tree/feature/SETO/lv_network/LVTestCaseNorthAmerican) for updates to the base model.
* See [Paper](https://doi.org/10.1109/PESGM.2014.6939794) for a description of the base model.

Use the version in _SecPar.dss_ for i2x.

## Directory of Files

* _buscoords.dat_ contains XY coordinates for the buses.
* _energy\_meters.dss_ adds energy meters for the primary feeders and secondary loads.
* _Master.dss_ the full-order version, with each secondary cable represented individually.
* _network\_protectors.dss_ adds relays to simulate network protectors (NWP) tripping on reverse power flow.
* _SecPar.dss_ a reduced-order version with parallel equivalents for secondary cables; used in i2x.

