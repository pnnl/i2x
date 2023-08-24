# Bulk Electric System (BES) Analysis for i2x 

This repository contains Matpower scripts for BES hosting
capacity analysis, used in sprint studies for the i2x roadmap.
Prerequisites include: 
 
- [Octave 8.2](https://octave.org/download). MATLAB could also work, but Octave is free, has a smaller footprint, and includes the GLPK solver.

- [Matpower 7.1](https://matpower.org/). Install and test in Octave as directed, choosing option 3 to save the Matpower paths within Octave.

The test systems are based on [CIMHub/BES](https://github.com/GRIDAPPSD/CIMHub/blob/feature/SETO/BES). To run a simulation:

- `python mpow.py [#]` where **#** is 0 for the IEEE 118-bus case, or 1 for the WECC 240-bus case, defaults to 0. Produces output in txt files.

## Hosting Capacity Analysis (HCA)

To run HCA on the IEEE 118-bus test system, configured with five N-1 contingencies:

- **python hca\_prep.py 0**
- Full N-1 HCA: **python hca.py IEEE118\_prep.json**
- Faster 1-bus, N-0 test case: **python hca.py test\_118.json**

To run HCA on the WECC 240-bus test system, configured with two N-1 contingencies:

- **python hca\_prep.py 1**
- Full N-1 HCA: **python hca.py WECC240\_prep.json**
- Faster 1-bus, N-0 test case: **python hca.py test\_240.json**

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
- **most.py** solves MOST base case for IEEE 118-bus (default, or argument=0) or WECC 240-bus test system (argument=1).
- **mpow.py** solves Matpower AC power flow base case for IEEE 118-bus (default, or argument=0) or WECC 240-bus test system (argument=1).
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

## Sample Results - IEEE118

The following simulation took a few minutes to run on the IEEE118 system. Results
are saved to *IEEE118\_out.json* after each bus analysis, in case one of them
fails to converge with iterations that don't terminate in Octave.

```
System: hca with nominal load=4.242 GW, actual load=2.863 GW, existing generation=8.619 GW
HCA generator index = 76, load_scale=0.6748, checking 118 buses with 0 grid upgrades
Bus Generation by Fuel[GW]
        hca    wind   solar nuclear   hydro    coal      ng      dl  [Max muF Branch] [Mean muF Branch]
  1   0.298   0.429   1.364   0.000   0.000   0.000   0.771   0.000  [72.3005 on 37] [12.0501 on 37]
  2   0.249   0.429   1.364   0.000   0.000   0.000   0.820   0.000  [60.0184 on 53] [10.0031 on 53]
  3   0.421   0.429   1.364   0.000   0.000   0.000   0.649   0.000  [94.3440 on 69] [15.7240 on 69]
  4   0.267   0.429   1.364   0.000   0.000   0.000   0.802   0.000  [54.6140 on 89] [9.1023 on 89]
  5   0.907   0.429   1.364   0.000   0.000   0.000   0.162   0.000  [50.2383 on 249] [8.3730 on 249]
  6   0.349   0.429   1.364   0.000   0.000   0.000   0.720   0.000  [44.5000 on 106] [7.4167 on 106]
  7   0.289   0.427   1.364   0.000   0.000   0.000   0.781   0.000  [218.4183 on 32] [36.4031 on 32]
  8   1.007   0.429   1.364   0.000   0.000   0.000   0.062   0.000  [50.7934 on 249] [8.4656 on 249]
  9   1.007   0.429   1.364   0.000   0.000   0.000   0.062   0.000  [50.7934 on 249] [8.4656 on 249]
 10   1.007   0.429   1.364   0.000   0.000   0.000   0.062   0.000  [50.7934 on 249] [8.4656 on 249]
 11   0.448   0.429   1.364   0.000   0.000   0.000   0.621   0.000  [102.5833 on 19] [17.0972 on 19]
 12   0.534   0.429   1.364   0.000   0.000   0.000   0.535   0.000  [115.2938 on 19] [19.2156 on 19]
 13   0.239   0.429   1.364   0.000   0.000   0.000   0.831   0.000  [67.3110 on 20] [11.2185 on 20]
 14   0.289   0.429   1.364   0.000   0.000   0.000   0.780   0.000  [72.1961 on 22] [12.0327 on 22]
 15   0.747   0.429   1.302   0.000   0.000   0.000   0.386   0.000  [113.3841 on 204] [18.8974 on 204]
 16   0.303   0.429   1.364   0.000   0.000   0.000   0.767   0.000  [80.1921 on 23] [13.3653 on 23]
 17   0.519   0.429   1.364   0.000   0.000   0.000   0.550   0.000  [90.9162 on 204] [15.1527 on 204]
 18   0.353   0.429   1.291   0.000   0.000   0.000   0.789   0.000  [110.4480 on 33] [18.4080 on 33]
 19   0.470   0.429   1.315   0.000   0.000   0.000   0.649   0.000  [72.1223 on 27] [12.0204 on 27]
 20   0.197   0.429   1.364   0.000   0.000   0.000   0.872   0.000  [67.6160 on 34] [11.2693 on 34]
 21   0.229   0.429   1.364   0.000   0.000   0.000   0.840   0.000  [86.7884 on 38] [14.4647 on 38]
 22   0.312   0.429   1.364   0.000   0.000   0.000   0.757   0.000  [128.3774 on 39] [21.3962 on 39]
 23   0.960   0.348   1.262   0.000   0.000   0.000   0.292   0.000  [112.8188 on 45] [18.8031 on 45]
 24   0.624   0.403   1.364   0.000   0.000   0.000   0.471   0.000  [91.2682 on 41] [15.2114 on 41]
 25   0.624   0.429   1.364   0.000   0.000   0.000   0.445   0.000  [83.3236 on 201] [13.8873 on 201]
 26   0.940   0.429   1.364   0.000   0.000   0.000   0.130   0.000  [51.3440 on 201] [8.5573 on 201]
 27   0.573   0.325   1.364   0.000   0.000   0.000   0.600   0.000  [186.9070 on 32] [31.1512 on 32]
 28   0.298   0.429   1.364   0.000   0.000   0.000   0.772   0.000  [66.4930 on 49] [11.0822 on 49]
 29   0.239   0.429   1.364   0.000   0.000   0.000   0.830   0.000  [61.6805 on 52] [10.2801 on 52]
 30   1.354   0.368   1.140   0.000   0.000   0.000   0.000   0.000  [2.2982 on 204] [0.3830 on 204]
 31   0.271   0.367   1.364   0.000   0.000   0.000   0.861   0.000  [100.5932 on 32] [16.7655 on 32]
 32   0.750   0.429   1.064   0.000   0.000   0.000   0.619   0.000  [186.5901 on 56] [31.0984 on 56]
 33   0.318   0.429   1.364   0.000   0.000   0.000   0.751   0.000  [83.2826 on 58] [13.8804 on 58]
 34   0.519   0.429   1.364   0.000   0.000   0.000   0.550   0.000  [65.6103 on 60] [10.9351 on 60]
 35   0.314   0.429   1.364   0.000   0.000   0.000   0.756   0.000  [82.6471 on 62] [13.7745 on 62]
 36   0.294   0.429   1.364   0.000   0.000   0.000   0.775   0.000  [68.9974 on 59] [11.4996 on 59]
 37   0.697   0.429   1.364   0.000   0.000   0.000   0.372   0.000  [79.1644 on 211] [13.1941 on 211]
 38   0.921   0.429   1.364   0.000   0.000   0.000   0.148   0.000  [56.9117 on 211] [9.4853 on 211]
 39   0.332   0.429   1.364   0.000   0.000   0.000   0.737   0.000  [44.5191 on 64] [7.4198 on 64]
 40   0.588   0.429   1.364   0.000   0.000   0.000   0.481   0.000  [108.2957 on 67] [18.0493 on 67]
 41   0.321   0.429   1.364   0.000   0.000   0.000   0.748   0.000  [58.7699 on 70] [9.7950 on 70]
 42   0.530   0.429   1.364   0.000   0.000   0.000   0.540   0.000  [89.8993 on 72] [14.9832 on 72]
 43   0.326   0.429   1.364   0.000   0.000   0.000   0.743   0.000  [44.6129 on 61] [7.4355 on 61]
 44   0.238   0.429   1.364   0.000   0.000   0.000   0.831   0.000  [70.6773 on 75] [11.7795 on 75]
 45   0.404   0.429   1.364   0.000   0.000   0.000   0.666   0.000  [107.9174 on 77] [17.9862 on 77]
 46   0.430   0.429   1.364   0.000   0.000   0.000   0.639   0.000  [106.8985 on 78] [17.8164 on 78]
 47   0.277   0.429   1.364   0.000   0.000   0.000   0.792   0.000  [77.9323 on 80] [12.9887 on 80]
 48   0.218   0.429   1.364   0.000   0.000   0.000   0.852   0.000  [54.2938 on 82] [9.0490 on 82]
 49   0.851   0.429   1.364   0.000   0.000   0.000   0.219   0.000  [80.7980 on 86] [13.4663 on 86]
 50   0.264   0.429   1.364   0.000   0.000   0.000   0.805   0.000  [58.8379 on 83] [9.8063 on 83]
 51   0.378   0.429   1.364   0.000   0.000   0.000   0.692   0.000  [83.9530 on 84] [13.9922 on 84]
 52   0.250   0.429   1.364   0.000   0.000   0.000   0.819   0.000  [62.4310 on 91] [10.4052 on 91]
 53   0.270   0.429   1.364   0.000   0.000   0.000   0.799   0.000  [68.0516 on 94] [11.3419 on 94]
 54   0.702   0.429   1.259   0.000   0.000   0.000   0.473   0.000  [89.9797 on 96] [14.9966 on 96]
 55   0.292   0.429   1.352   0.000   0.000   0.000   0.789   0.000  [70.5504 on 98] [11.7584 on 98]
 56   0.963   0.429   1.364   0.000   0.000   0.000   0.106   0.000  [312.5027 on 84] [52.0838 on 84]
 57   0.288   0.429   1.364   0.000   0.000   0.000   0.782   0.000  [75.6717 on 100] [12.6120 on 100]
 58   0.319   0.429   1.364   0.000   0.000   0.000   0.750   0.000  [81.0768 on 101] [13.5128 on 101]
 59   0.899   0.429   1.364   0.000   0.000   0.000   0.170   0.000  [90.8452 on 226] [15.1409 on 226]
 60   0.634   0.429   1.364   0.000   0.000   0.000   0.436   0.000  [65.4272 on 107] [10.9045 on 107]
 61   0.822   0.429   1.364   0.000   0.000   0.000   0.247   0.000  [74.0144 on 227] [12.3357 on 227]
 62   0.495   0.429   1.364   0.000   0.000   0.000   0.574   0.000  [106.4459 on 109] [17.7410 on 109]
 63   0.816   0.429   1.364   0.000   0.000   0.000   0.254   0.000  [80.5191 on 226] [13.4198 on 226]
 64   1.082   0.429   1.351   0.000   0.000   0.000   0.000   0.000  [5.1367 on 226] [0.8561 on 226]
 65   1.035   0.429   1.364   0.000   0.000   0.000   0.035   0.000  [105.8907 on 86] [17.6484 on 86]
 66   0.600   0.429   1.364   0.000   0.000   0.000   0.469   0.000  [51.4128 on 229] [8.5688 on 229]
 67   0.333   0.429   1.364   0.000   0.000   0.000   0.736   0.000  [44.6670 on 115] [7.4445 on 115]
 68   1.181   0.429   1.252   0.000   0.000   0.000   0.000   0.000  [2.1877 on 231] [0.3646 on 231]
 69   0.689   0.429   1.315   0.000   0.000   0.000   0.430   0.000  [67.5716 on 231] [11.2619 on 231]
 70   0.774   0.429   1.357   0.000   0.000   0.000   0.303   0.000  [99.2967 on 231] [16.5495 on 231]
 71   0.209   0.429   1.364   0.000   0.000   0.000   0.860   0.000  [52.2859 on 122] [8.7143 on 122]
 72   0.320   0.429   1.364   0.000   0.000   0.000   0.749   0.000  [45.2728 on 45] [7.5455 on 45]
 73   0.161   0.429   1.364   0.000   0.000   0.000   0.908   0.000  [44.5000 on 126] [7.4167 on 126]
 74   0.307   0.429   1.364   0.000   0.000   0.000   0.762   0.000  [61.7052 on 127] [10.2842 on 127]
 75   0.859   0.429   1.323   0.000   0.000   0.000   0.251   0.000  [75.5674 on 127] [12.5946 on 127]
 76   0.351   0.429   1.354   0.000   0.000   0.000   0.729   0.000  [77.7840 on 130] [12.9640 on 130]
 77   1.042   0.290   1.095   0.000   0.000   0.000   0.436   0.000  [73.1810 on 243] [12.1968 on 243]
 78   0.460   0.429   1.310   0.000   0.000   0.000   0.664   0.000  [80.0334 on 243] [13.3389 on 243]
 79   0.262   0.429   1.362   0.000   0.000   0.000   0.810   0.000  [135.0882 on 243] [22.5147 on 243]
 80   0.321   0.429   1.364   0.000   0.000   0.000   0.748   0.000  [72.8534 on 243] [12.1422 on 243]
 81   1.250   0.403   1.209   0.000   0.000   0.000  -0.000   0.000  [4.0188 on 136] [0.6698 on 136]
 82   0.517   0.290   1.364   0.000   0.000   0.000   0.692   0.000  [68.0965 on 134] [11.3494 on 134]
 83   0.411   0.410   1.364   0.000   0.000   0.000   0.677   0.000  [67.5139 on 134] [11.2523 on 134]
 84   0.303   0.429   1.364   0.000   0.000   0.000   0.766   0.000  [88.0023 on 146] [14.6670 on 146]
 85   0.467   0.423   1.320   0.000   0.000   0.000   0.653   0.000  [63.9068 on 243] [10.6511 on 243]
 86   0.171   0.429   1.364   0.000   0.000   0.000   0.898   0.000  [44.5000 on 147] [7.4167 on 147]
 87   0.157   0.429   1.364   0.000   0.000   0.000   0.912   0.000  [44.5000 on 150] [7.4167 on 150]
 88   0.330   0.429   1.364   0.000   0.000   0.000   0.739   0.000  [92.2810 on 148] [15.3802 on 148]
 89   0.580   0.429   1.197   0.000   0.000   0.000   0.657   0.000  [68.5002 on 243] [11.4167 on 243]
 90   0.538   0.403   1.258   0.000   0.000   0.000   0.664   0.000  [70.1389 on 243] [11.6898 on 243]
 91   0.220   0.429   1.364   0.000   0.000   0.000   0.850   0.000  [117.9202 on 156] [19.6534 on 156]
 92   0.506   0.418   1.157   0.000   0.000   0.000   0.782   0.000  [167.5944 on 165] [27.9324 on 165]
 93   0.233   0.429   1.364   0.000   0.000   0.000   0.837   0.000  [72.1275 on 162] [12.0213 on 162]
 94   0.220   0.429   1.364   0.000   0.000   0.000   0.849   0.000  [140.7733 on 165] [23.4622 on 165]
 95   0.165   0.429   1.364   0.000   0.000   0.000   0.905   0.000  [79.7720 on 166] [13.2953 on 166]
 96   0.561   0.409   1.222   0.000   0.000   0.000   0.671   0.000  [65.9335 on 243] [10.9889 on 243]
 97   0.199   0.429   1.364   0.000   0.000   0.000   0.870   0.000  [75.4191 on 139] [12.5698 on 139]
 98   0.116   0.429   1.364   0.000   0.000   0.000   0.953   0.000  [63.3942 on 140] [10.5657 on 140]
 99   0.171   0.429   1.364   0.000   0.000   0.000   0.898   0.000  [100.0616 on 141] [16.6769 on 141]
100   0.869   0.269   0.861   0.000   0.000   0.000   0.863   0.000  [192.5147 on 169] [32.0858 on 169]
101   0.313   0.402   1.323   0.000   0.000   0.000   0.825   0.000  [192.0117 on 169] [32.0020 on 169]
102   0.201   0.429   1.364   0.000   0.000   0.000   0.868   0.000  [62.9142 on 159] [10.4857 on 159]
103   0.309   0.429   1.262   0.000   0.000   0.000   0.863   0.000  [180.1876 on 169] [30.0313 on 169]
104   0.460   0.402   1.137   0.000   0.000   0.000   0.863   0.000  [190.3516 on 169] [31.7253 on 169]
105   0.624   0.376   0.999   0.000   0.000   0.000   0.863   0.000  [190.3516 on 169] [31.7253 on 169]
106   0.383   0.429   1.187   0.000   0.000   0.000   0.863   0.000  [190.3516 on 169] [31.7253 on 169]
107   0.348   0.417   1.235   0.000   0.000   0.000   0.863   0.000  [190.3516 on 169] [31.7253 on 169]
108   0.184   0.429   1.364   0.000   0.000   0.000   0.885   0.000  [61.6914 on 12] [10.2819 on 12]
109   0.202   0.429   1.364   0.000   0.000   0.000   0.868   0.000  [68.1735 on 14] [11.3622 on 14]
110   0.344   0.429   1.198   0.000   0.000   0.000   0.892   0.000  [84.1653 on 8] [14.0276 on 8]
111   0.157   0.429   1.364   0.000   0.000   0.000   0.912   0.000  [44.5000 on 16] [7.4167 on 16]
112   0.344   0.429   1.198   0.000   0.000   0.000   0.892   0.000  [84.1653 on 8] [14.0276 on 8]
113   0.114   0.429   1.364   0.000   0.000   0.000   0.956   0.000  [53.6931 on 30] [8.9489 on 30]
114   0.313   0.403   1.357   0.000   0.000   0.000   0.789   0.000  [227.3392 on 56] [37.8899 on 56]
115   0.323   0.399   1.356   0.000   0.000   0.000   0.784   0.000  [215.4626 on 56] [35.9104 on 56]
116   1.181   0.429   1.252   0.000   0.000   0.000   0.000   0.000  [2.1877 on 231] [0.3646 on 231]
117   0.170   0.429   1.364   0.000   0.000   0.000   0.899   0.000  [44.5000 on 21] [7.4167 on 21]
118   0.293   0.429   1.364   0.000   0.000   0.000   0.776   0.000  [60.9332 on 128] [10.1555 on 128]

Writing HCA results to IEEE118_out.json

Branches At Limit:
 idx From   To     muF     MVA     kV1     kV2
   1  100  101  0.0077  157.00  138.00  138.00
   2  100  103  0.0032  314.00  138.00  138.00
   3  100  104  0.0014  157.00  138.00  138.00
   4  100  106  0.0004  157.00  138.00  138.00
   8  103  110  0.1454  157.00  138.00  138.00
   9  104  105  0.0011  157.00  138.00  138.00
  10  105  106  0.0005  157.00  138.00  138.00
  11  105  107  0.0004  157.00  138.00  138.00
  12  105  108  0.0533  157.00  138.00  138.00
  13  106  107  0.0004  157.00  138.00  138.00
  14  108  109  0.0589  157.00  138.00  138.00
  16  110  111  0.0384  157.00  138.00  138.00
  19   11   12  0.1881  157.00  138.00  138.00
  20   11   13  0.0581  157.00  138.00  138.00
  21   12  117  0.0384  157.00  138.00  138.00
  22   12   14  0.0623  157.00  138.00  138.00
  23   12   16  0.0693  157.00  138.00  138.00
  27   15   19  0.0761  157.00  138.00  138.00
  30   17  113  0.0464  157.00  138.00  138.00
  32   17   31  0.6748  157.00  138.00  138.00
  33   18   19  0.0954  157.00  138.00  138.00
  34   19   20  0.0584  157.00  138.00  138.00
  35   19   34  0.0531  157.00  138.00  138.00
  37    1    3  0.0624  157.00  138.00  138.00
  38   20   21  0.0749  157.00  138.00  138.00
  39   21   22  0.1109  157.00  138.00  138.00
  41   23   24  0.0812  314.00  138.00  138.00
  45   24   72  0.1370  157.00  138.00  138.00
  48   27  115  0.0116  157.00  138.00  138.00
  49   27   28  0.0574  157.00  138.00  138.00
  52   29   31  0.0533  157.00  138.00  138.00
  53    2   12  0.0518  157.00  138.00  138.00
  56   32  113  0.5720  157.00  138.00  138.00
  57   32  114  0.0056  157.00  138.00  138.00
  58   33   37  0.0719  157.00  138.00  138.00
  59   34   36  0.0596  157.00  138.00  138.00
  60   34   37  0.0567  314.00  138.00  138.00
  61   34   43  0.0385  157.00  138.00  138.00
  62   35   36  0.0714  157.00  138.00  138.00
  64   37   39  0.0384  157.00  138.00  138.00
  67   39   40  0.1319  157.00  138.00  138.00
  69    3    5  0.0815  157.00  138.00  138.00
  70   40   41  0.0508  157.00  138.00  138.00
  72   41   42  0.0776  157.00  138.00  138.00
  73   42   49  0.0381  157.00  138.00  138.00
  74   43   44  0.0382  157.00  138.00  138.00
  75   44   45  0.0610  157.00  138.00  138.00
  77   45   49  0.0932  157.00  138.00  138.00
  78   46   47  0.0923  157.00  138.00  138.00
  80   47   49  0.0673  157.00  138.00  138.00
  82   48   49  0.0469  157.00  138.00  138.00
  83   49   50  0.0508  157.00  138.00  138.00
  84   49   51  0.3424  157.00  138.00  138.00
  86   49   66  0.2030  157.00  138.00  138.00
  89    4    5  0.0472  157.00  138.00  138.00
  91   51   52  0.0539  157.00  138.00  138.00
  94   53   54  0.0588  157.00  138.00  138.00
  96   54   56  0.0777  314.00  138.00  138.00
  98   55   56  0.1064  157.00  138.00  138.00
 100   56   57  0.0653  157.00  138.00  138.00
 101   56   58  0.0700  157.00  138.00  138.00
 106    5    6  0.0384  157.00  138.00  138.00
 107   60   61  0.0565  314.00  138.00  138.00
 109   61   62  0.0919  157.00  138.00  138.00
 111   62   67  0.0383  157.00  138.00  138.00
 115   66   67  0.0386  157.00  138.00  138.00
 121    6    7  0.0384  157.00  138.00  138.00
 122   70   71  0.0452  157.00  138.00  138.00
 124   70   75  0.0537  157.00  138.00  138.00
 125   71   72  0.0381  157.00  138.00  138.00
 126   71   73  0.0384  157.00  138.00  138.00
 127   74   75  0.1185  157.00  138.00  138.00
 128   75  118  0.0526  157.00  138.00  138.00
 130   76  118  0.0672  157.00  138.00  138.00
 132   77   78  0.0150  314.00  138.00  138.00
 134   77   82  0.1283  314.00  138.00  138.00
 135   78   79  0.0679  157.00  138.00  138.00
 136   79   80  0.0035  157.00  138.00  138.00
 137    7   12  0.1489  157.00  138.00  138.00
 139   80   97  0.0651  157.00  138.00  138.00
 140   80   98  0.0547  157.00  138.00  138.00
 141   80   99  0.0864  157.00  138.00  138.00
 142   82   83  0.0019  314.00  138.00  138.00
 145   83   85  0.0034  157.00  138.00  138.00
 146   84   85  0.0760  157.00  138.00  138.00
 147   85   86  0.0384  157.00  138.00  138.00
 148   85   88  0.0797  157.00  138.00  138.00
 150   86   87  0.0384  157.00  138.00  138.00
 151   88   89  0.0143  157.00  138.00  138.00
 156   90   91  0.1067  157.00  138.00  138.00
 159   92  102  0.0543  157.00  138.00  138.00
 162   93   94  0.0623  157.00  138.00  138.00
 165   94   96  0.2663  157.00  138.00  138.00
 166   95   96  0.0689  157.00  138.00  138.00
 167   96   97  0.0157  157.00  138.00  138.00
 169   99  100  1.1608  157.00  138.00  138.00
 173  100  179  0.5653   41.60  138.00   13.80
 174  100  180  0.5653  160.00  138.00   13.80
 177  104  183  0.5653  186.40  138.00   13.80
 179  105  185  0.3406  108.80  138.00   13.80
 183  110  188  0.1427  101.20  138.00   13.80
 191   15  126  0.6729   53.60  138.00   13.80
 193   18  128  0.2593   73.20  138.00   13.80
 195   19  130  0.6203   49.60  138.00   13.80
 198   24  132  0.3143   26.00  138.00   13.80
 200   26  134  0.0016  153.00  345.00   13.80
 201   26   25  0.1591  261.78  345.00  138.00
 203   27  136  0.2985   41.60  138.00   13.80
 204   30   17  0.1784  257.73  345.00  138.00
 206   31  138  0.4211   62.00  138.00   13.80
 209   34  141  0.0098  115.00  138.00   13.80
 211   38   37  0.1175  266.67  345.00  138.00
 212   40  143  0.0091  115.00  138.00   13.80
 216    4  120  0.0146  115.00  138.00   13.80
 219   54  149  0.6023  105.60  138.00   13.80
 220   55  150  0.0154  115.00  138.00   13.80
 221   55  151  0.6506   12.00  138.00   13.80
 226   63   59  0.1524  259.07  345.00  138.00
 227   64   61  0.0639  373.13  345.00  138.00
 228   65  156  0.0006  220.00  345.00   13.80
 229   65   66  0.0444  270.27  345.00  138.00
 231   68   69  0.2048  270.27  345.00  138.00
 233   69  159  0.6699   49.60  138.00   13.80
 240   76  165  0.6308   10.00  138.00   13.80
 243   81   80  0.5731  270.27  345.00  138.00
 244   82  168  0.5981  139.20  138.00   13.80
 249    8    5  0.1750  374.53  345.00  138.00
 253   92  175  0.5774  207.60  138.00   13.80
Writing HCA results to IEEE118_out.json
```

To summarize actionable results from this IEEE118 HCA analysis:

- **python grid\_upgrades.py 0**

The first several lines of output follow. At bus 1, the hosting capacity 
is 298 MW. To increase this limit, the single-circuit 138-kV line between 
buses 20 and 21 might be upgraded. For example, a second line of the same
impedance and MVA rating might be constructed in parallel. At bus 5, the
hosting capacity is 907 MW. To increase that limit, upgrading the 138/13.8
kV transformer between buses 90 and 172 might be upgraded. For example, a
second 115-MVA transformer might be added in parallel.


```
 Bus   HC[GW]
   1    0.298
       Max Mu Branch:   37 (  72.301) Line  20- 21  138.00 kV x=0.0849, z=377.56 ohms, npar=1, mva=157.00, mi=20.21
      Mean Mu Branch:   37 (  12.050) Line  20- 21  138.00 kV x=0.0849, z=377.56 ohms, npar=1, mva=157.00, mi=20.21
   2    0.249
       Max Mu Branch:   53 (  60.018) Line  30- 38  345.00 kV x=0.0540, z=425.77 ohms, npar=1, mva=1084.00, mi=107.12
      Mean Mu Branch:   53 (  10.003) Line  30- 38  345.00 kV x=0.0540, z=425.77 ohms, npar=1, mva=1084.00, mi=107.12
   3    0.421
       Max Mu Branch:   69 (  94.344) Line  40- 41  138.00 kV x=0.0487, z=380.18 ohms, npar=1, mva=157.00, mi=11.59
      Mean Mu Branch:   69 (  15.724) Line  40- 41  138.00 kV x=0.0487, z=380.18 ohms, npar=1, mva=157.00, mi=11.59
   4    0.267
       Max Mu Branch:   89 (  54.614) Line  50- 57  138.00 kV x=0.1340, z=382.60 ohms, npar=1, mva=157.00, mi=31.90
      Mean Mu Branch:   89 (   9.102) Line  50- 57  138.00 kV x=0.1340, z=382.60 ohms, npar=1, mva=157.00, mi=31.90
   5    0.907
       Max Mu Branch:  249 (  50.238) Xfmr  90-172  138.00 /   13.80 kV x=0.0870, mva=115.00
      Mean Mu Branch:  249 (   8.373) Xfmr  90-172  138.00 /   13.80 kV x=0.0870, mva=115.00
```

## Sample Results - WECC240

The HCA analysis of 187 buses with two N-1 contingencies took 17 
minutes to run on the WECC240 system. Results are saved to 
*WECC240\_out.json*. At buses 67 and 226, the hosting capacity is zero.

To summarize actionable results from this IEEE118 HCA analysis:

- **python grid\_upgrades.py 0**

The first few lines of output follow. At bus 1, the hosting capacity is
estimated at 4247 MW. To increase this limit, the 500/230-kV transformer between
buses 203 and 205 might be upgraded from 552.49 MVA.

```
 Bus   HC[GW]
   1    4.247
       Max Mu Branch:  430 ( 186.695) Xfmr 203-205  500.00 /  230.00 kV x=0.0181, mva=552.49
      Mean Mu Branch:  430 (  62.232) Xfmr 203-205  500.00 /  230.00 kV x=0.0181, mva=552.49
```

## Allowable Number of Contingencies

The logic built in to *hca\_prep.py* identifies N-1 branch contingencies 
according to the branch MVA rating, i.e., the highest-capacity branches 
are included. In the reduced- order system models, most of these 
highest-capacity branches represent lines or transformers in parallel. 
Instead of removing the whole equivalent branch, the N-1 contingency 
represents the outage of one parallel component, i.e., the equivalent 
branch rating is reduced but not to zero. This logic probably doesn't 
represent the most severe contingencies for HCA, because the strongest 
parts of the system are weakened incrementally. A more realistic scheme, 
at least for impact studies, would select different contingency sets for 
each HCA bus, accounting for local network topology. For systematic HCA 
over the whole network, the automated contingency selection would be more 
practical. 

The following table illustrates how many contingencies, Nc, can be solved 
with Octave and the GLPK solver. At bus 1, higher values of Nc reduce the 
estimated hosting capacity by up to 5%. Over the whole set of possible HCA 
buses, higher values of Nc may have more effect on the estimated hosting 
capacity. Furthermore, custom contingency selections for each HCA bus 
would have more effect on the estimated hosting capacity. The results 
indicated that 39 contingencies are practical for the IEEE118 system, and 
at least 24 contingencies are practical for the WECC240 system. Those 
bounds might be increased in a more capable computer, or using a 
commercial solver. 


```
System     Smallest        Number of         Bus 1 Hosting     Solution
           Contingency     Contingencies     Capacity          Time
           Branch [MVA]    [Nc]              [MW]              [s]
           
IEEE118        2000            5                298                3
                400           11                287                7
                350           13                287                9
                300           32                287               39
                250           39                285               63
                150          179               -----out of memory-----
WECC240        7000            2               4247                4
               5000            5               4243                9
               4000            6               4243               18
               3500           24               4236              334
               3200           32               -----out of memory-----
```

The solution times were obtained in a Ubuntu Virtual Machine, allocated up to 8 GB RAM.
The CPU speed was benchmarked according to:

- *sudo apt-get install sysbench*
- *sysbench cpu run*
- resulting CPU speed is **1071.62** events per second

Copyright 2022-2023, Battelle Memorial Institute
