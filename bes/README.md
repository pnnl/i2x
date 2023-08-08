# Bulk Electric System (BES) Analysis for i2x 

This repository contains Matpower scripts for BES hosting
capacity analysis, used in sprint studies for the i2x roadmap.
Prerequisites include: 
 
- [Octave 8.2](https://octave.org/download). MATLAB could also work, but Octave is free, has a smaller footprint, and includes the GLPK solver.

- [Matpower 7.1](https://matpower.org/). Install and test in Octave as directed, choosing option 3 to save the Matpower paths within Octave.

The test systems are based on [CIMHub/BES](https://github.com/GRIDAPPSD/CIMHub/blob/feature/SETO/BES). To run a simulation:

- `python mpow.py [#]` where **#** is 0 for the IEEE 118-bus case, or 1 for the WECC 240-bus case, defaults to 0. Produces output in txt files.

## Hosting Capacity Analysis (HCA)

To run HCA on the IEEE 118-bus test system:

- **python3 hca\_prep.py 0**
- **python3 hca.py hca\_118.json**

To run HCA on the WECC 240-bus test system:

- **python3 hca\_prep.py 1**
- **python3 hca.py hca\_240.json**

## Directory of Script and Data Files

- **clean.bat** removes temporary output files on Windows
- **clean.sh** removes temporary output files on Linux and Mac OS X
- **hca\_118.json** configures load scaling, buses of interest, grid upgrades, and branch contingencies for hosting capacity analysis on the IEEE 118-bus system
- **hca\_240.json** configures load scaling, buses of interest, grid upgrades, and branch contingencies for hosting capacity analysis on the WECC 240-bus system
- **hca\_prep.py** reads a Matpower base case file, outputs the *wmva.m* with branch ratings and *\_prep.json* file with contingencies and buses for hosting capacity analysis.
- **hca.py** 
- **IEEE118.m** defines the IEEE 118-bus base case for Matpower
- **IEEE118\_Network.json** defines the network layout for plotting; file comes from CIMHub
- **IEEE118\_prep.json** defines the buses, branch contingencies, grid upgrades and load scaling for hosting capacity analysis of the IEEE 118-bus test system.  Overwritten by *hca\_prep.py*
- **IEEE118\_wmva.m** base case with branch MVA ratings. Overwritten by *hca\_prep.py*
- **matpower\_gen\_type.m** Matpower support function identifying solar and wind generators from type codes PV and WT. Not currently used.
- **most.py** functions like *mpow.py* but uses the *mpow\_utilities* module to replace local functions.
- **mpow.py** solves Matpower base case for IEEE 118-bus (default, or argument=0) or WECC 240-bus test system (argument=1).
- **plot\_bes.py** plots the network layout of the bulk electric system for IEEE 118-bus test system (default, or argument=0) or the WECC 240-bus test system (argument=1)
- **plot\_hca.py** plots the bus hosting capacity and branch congestion levels on a network layout
- **WECC240.m** defines the WECC 240-bus base case for Matpower
- **WECC240\_Network.json** defines the network layout for plotting; file comes from CIMHub
- **WECC240\_prep.json** defines the buses, branch contingencies, grid upgrades and load scaling for hosting capacity analysis of the WECC 240-bus test system.  Overwritten by *hca\_prep.py*
- **WECC240\_wmva.m** base case with branch MVA ratings. Overwritten by *hca\_prep.py*

Also, see the **tests/** sub-directory for 3-day unit commitment and hosting
capacity test cases on an 8-bus model of the ERCOT test system used for
the Distribution System Operation with Transactive (DSO+T) study.

Copyright 2022-2023, Battelle Memorial Institute

