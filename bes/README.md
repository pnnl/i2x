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

- **python3 hca\_prep.py IEEE118 200.0**
- Full N-1 HCA: **python3 hca.py IEEE118\_prep.json**
- Faster 1-bus, N-0 test case: **python3 hca.py test\_118.json**

To run HCA on the WECC 240-bus test system:

- **python3 hca\_prep.py WECC240 4000.0**
- Full N-1 HCA: **python3 hca.py WECC240\_prep.json**
- Faster 1-bus, N-0 test case: **python3 hca.py test\_240.json**

To run a single-bus HCA:


## Directory of Script and Data Files

- **clean.bat** removes temporary output files on Windows
- **clean.sh** removes temporary output files on Linux and Mac OS X
- **hca.py** call the HCA function, as configured by a JSON file name supplied as the first command-line argument
- **hca\_prep.py** reads a Matpower base case file, outputs the *wmva.m* with branch ratings and *\_prep.json* file with contingencies and buses for hosting capacity analysis.
- **IEEE118.m** defines the IEEE 118-bus base case for Matpower
- **IEEE118\_Network.json** defines the network layout for plotting; file comes from CIMHub
- **IEEE118\_prep.json** defines the buses, branch contingencies, grid upgrades and load scaling for hosting capacity analysis of the IEEE 118-bus test system.  Overwritten by *hca\_prep.py*
- **IEEE118\_wmva.m** base case with branch MVA ratings. Overwritten by *hca\_prep.py*
- **matpower\_gen\_type.m** Matpower support function identifying solar and wind generators from type codes PV and WT. Not currently used.
- **most.py** functions like *mpow.py* but uses the *mpow\_utilities* module to replace local functions.
- **mpow.py** solves Matpower base case for IEEE 118-bus (default, or argument=0) or WECC 240-bus test system (argument=1).
- **plot\_bes.py** plots the network layout of the bulk electric system for IEEE 118-bus test system (default, or argument=0) or the WECC 240-bus test system (argument=1)
- **plot\_hca.py** plots the bus hosting capacity and branch congestion levels on a network layout
- **test\_118.json** configures load scaling, buses of interest, grid upgrades, and branch contingencies for hosting capacity analysis for a 1-bus test case on the IEEE 118-bus system
- **test\_240.json** configures load scaling, buses of interest, grid upgrades, and branch contingencies for hosting capacity analysis for a 1-bus test case on the WECC 240-bus system
- **WECC240.m** defines the WECC 240-bus base case for Matpower
- **WECC240\_Network.json** defines the network layout for plotting; file comes from CIMHub
- **WECC240\_prep.json** defines the buses, branch contingencies, grid upgrades and load scaling for hosting capacity analysis of the WECC 240-bus test system.  Overwritten by *hca\_prep.py*
- **WECC240\_wmva.m** base case with branch MVA ratings. Overwritten by *hca\_prep.py*

Also, see the **tests/** sub-directory for 3-day unit commitment and hosting
capacity test cases on an 8-bus model of the ERCOT test system used for
the Distribution System Operation with Transactive (DSO+T) study.

## Sample Results

The following output took 2:44, and appeared to have stalled at the next bus.

```
System: hca with nominal load=4.242 GW, actual load=4.242 GW, existing generation=8.619 GW
HCA generator index = 76, load_scale=1.0000, checking 118 buses with 0 grid upgrades
Bus Generation by Fuel[GW]
        hca    wind   solar nuclear   hydro    coal      ng      dl  [Max muF Branch] [Mean muF Branch]
  1   0.301   0.429   1.364   0.000   0.000   0.000   2.147   0.000  [76.2420 on 37] [1.9060 on 37]
  2   0.264   0.429   1.364   0.000   0.000   0.000   2.185   0.000  [59.8317 on 53] [1.4958 on 53]
  3   0.452   0.429   1.364   0.000   0.000   0.000   1.997   0.000  [111.4321 on 69] [2.7946 on 69]
  4   0.280   0.429   1.364   0.000   0.000   0.000   2.169   0.000  [68.7487 on 89] [1.7187 on 89]
  5   0.576   0.429   1.364   0.000   0.000   0.000   1.873   0.000  [100.5969 on 105] [2.5149 on 105]
  6   0.324   0.429   1.364   0.000   0.000   0.000   2.124   0.000  [48.7033 on 121] [2.0806 on 121]
  7   0.281   0.429   1.364   0.000   0.000   0.000   2.168   0.000  [71.6046 on 137] [1.7901 on 137]
  8   0.403   0.429   1.364   0.000   0.000   0.000   2.046   0.000  [44.5000 on 249] [1.1125 on 249]
  9   0.403   0.429   1.364   0.000   0.000   0.000   2.046   0.000  [44.5000 on 249] [1.1125 on 249]
 10   0.403   0.429   1.364   0.000   0.000   0.000   2.046   0.000  [44.5000 on 249] [1.1125 on 249]
 11   0.358   0.429   1.364   0.000   0.000   0.000   2.091   0.000  [76.3627 on 19] [1.9091 on 19]
 12   0.542   0.429   1.364   0.000   0.000   0.000   1.907   0.000  [90.8713 on 19] [2.2718 on 19]
 13   0.256   0.429   1.364   0.000   0.000   0.000   2.192   0.000  [67.0279 on 20] [1.6757 on 20]
 14   0.245   0.429   1.364   0.000   0.000   0.000   2.204   0.000  [71.5356 on 22] [1.7884 on 22]
 15   0.755   0.429   1.311   0.000   0.000   0.000   1.747   0.000  [53.7961 on 26] [1.3449 on 26]
 16   0.244   0.429   1.364   0.000   0.000   0.000   2.205   0.000  [77.5904 on 23] [1.9398 on 23]
 17   0.609   0.429   1.364   0.000   0.000   0.000   1.840   0.000  [79.9641 on 204] [1.9991 on 204]
 18   0.351   0.429   1.291   0.000   0.000   0.000   2.171   0.000  [54.0266 on 31] [1.3507 on 31]
 19   0.444   0.429   1.315   0.000   0.000   0.000   2.054   0.000  [108.2548 on 27] [2.7064 on 27]
 20   0.231   0.429   1.364   0.000   0.000   0.000   2.218   0.000  [64.4576 on 34] [1.6114 on 34]
 21   0.257   0.429   1.364   0.000   0.000   0.000   2.191   0.000  [79.2873 on 38] [1.9822 on 38]
 22   0.309   0.429   1.364   0.000   0.000   0.000   2.140   0.000  [51.6403 on 39] [1.2910 on 39]
 23   0.639   0.422   1.255   0.000   0.000   0.000   1.926   0.000  [57.9505 on 56] [1.4488 on 56]
 24   0.429   0.399   1.364   0.000   0.000   0.000   2.050   0.000  [173.5101 on 32] [4.3378 on 32]
 25   0.460   0.429   1.364   0.000   0.000   0.000   1.988   0.000  [55.3573 on 42] [1.3839 on 42]
 26   0.262   0.416   1.330   0.000   0.000   0.000   2.235   0.000  [276.1694 on 86] [6.9042 on 86]
 27   0.540   0.325   1.353   0.000   0.000   0.000   2.024   0.000  [84.0370 on 32] [2.1009 on 32]
 28   0.299   0.429   1.364   0.000   0.000   0.000   2.150   0.000  [65.9142 on 49] [1.6479 on 49]
 29   0.241   0.429   1.364   0.000   0.000   0.000   2.208   0.000  [60.5883 on 52] [1.5147 on 52]
 30   0.599   0.429   1.364   0.000   0.000   0.000   1.850   0.000  [62.6962 on 204] [2.3795 on 204]
 31   0.337   0.367   1.364   0.000   0.000   0.000   2.173   0.000  [95.0875 on 32] [2.3772 on 32]
 32   0.701   0.429   1.064   0.000   0.000   0.000   2.048   0.000  [117.6424 on 56] [2.9411 on 56]
 33   0.313   0.429   1.364   0.000   0.000   0.000   2.135   0.000  [47.9221 on 28] [1.1981 on 28]
 34   0.371   0.429   1.364   0.000   0.000   0.000   2.078   0.000  [73.9595 on 60] [1.8490 on 60]
 35   0.306   0.429   1.364   0.000   0.000   0.000   2.142   0.000  [82.8324 on 62] [2.0708 on 62]
 36   0.304   0.429   1.364   0.000   0.000   0.000   2.145   0.000  [69.1312 on 59] [1.7283 on 59]
 37   0.800   0.429   1.364   0.000   0.000   0.000   1.648   0.000  [81.1400 on 58] [2.0285 on 58]
 38   0.504   0.429   1.364   0.000   0.000   0.000   1.944   0.000  [55.3606 on 211] [2.3140 on 211]
 39   0.335   0.429   1.364   0.000   0.000   0.000   2.113   0.000  [44.9382 on 64] [1.1235 on 64]
 40   0.601   0.429   1.364   0.000   0.000   0.000   1.848   0.000  [98.7790 on 67] [2.4695 on 67]
 41   0.316   0.429   1.364   0.000   0.000   0.000   2.133   0.000  [70.4730 on 70] [1.7618 on 70]
 42   0.536   0.429   1.364   0.000   0.000   0.000   1.913   0.000  [140.3207 on 73] [3.5080 on 73]
 43   0.294   0.423   1.364   0.000   0.000   0.000   2.161   0.000  [259.1956 on 32] [6.4799 on 32]
 44   0.259   0.429   1.364   0.000   0.000   0.000   2.190   0.000  [74.0072 on 75] [1.8502 on 75]
 45   0.420   0.429   1.364   0.000   0.000   0.000   2.029   0.000  [112.7787 on 77] [2.8195 on 77]
 46   0.444   0.429   1.364   0.000   0.000   0.000   2.005   0.000  [108.7305 on 78] [2.7183 on 78]
 47   0.330   0.429   1.364   0.000   0.000   0.000   2.119   0.000  [79.3286 on 80] [1.9832 on 80]
 48   0.235   0.429   1.364   0.000   0.000   0.000   2.214   0.000  [54.6321 on 82] [1.3658 on 82]
 49   1.060   0.429   1.364   0.000   0.000   0.000   1.389   0.000  [105.0766 on 86] [2.6269 on 86]
 50   0.271   0.429   1.364   0.000   0.000   0.000   2.178   0.000  [62.5434 on 83] [1.5636 on 83]
 51   0.409   0.429   1.364   0.000   0.000   0.000   2.039   0.000  [63.6237 on 92] [1.5906 on 92]
 52   0.256   0.429   1.364   0.000   0.000   0.000   2.193   0.000  [64.0119 on 91] [1.6003 on 91]
 53   0.250   0.422   1.364   0.000   0.000   0.000   2.205   0.000  [294.9168 on 169] [7.3729 on 169]
 54   0.443   0.429   1.259   0.000   0.000   0.000   2.112   0.000  [103.1354 on 96] [2.5784 on 96]
 55   0.272   0.428   1.352   0.000   0.000   0.000   2.190   0.000  [180.3086 on 32] [4.5077 on 32]
 56   0.710   0.385   1.364   0.000   0.000   0.000   1.783   0.000  [394.0387 on 96] [9.8510 on 96]
```

Copyright 2022-2023, Battelle Memorial Institute

