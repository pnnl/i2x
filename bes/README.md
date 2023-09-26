# Bulk Electric System (BES) Analysis for i2x 

This repository contains Matpower scripts for BES hosting
capacity analysis, used in sprint studies for the i2x roadmap.
Prerequisites include: 
 
- [Octave 8.2](https://octave.org/download). MATLAB could also work, but Octave is free, has a smaller footprint, and includes the GLPK solver.

- [Matpower 7.1](https://matpower.org/). Install and test in Octave as directed, choosing option 3 to save the Matpower paths within Octave.

The test systems are based on [CIMHub/BES](https://github.com/GRIDAPPSD/CIMHub/blob/feature/SETO/BES). To run a base-case simulation in Matpower or MOST:

- `python mpow.py [#]` where **#** is 0 for the IEEE 118-bus case, or 1 for the WECC 240-bus case, defaults to 0. Produces output in txt files.
- `python most.py [#]` where **#** is 0 for the IEEE 118-bus case, or 1 for the WECC 240-bus case, defaults to 0. Produces output in txt files.

## Directory of Script and Data Files

- **bes\_cases.py** contains shared configuration data for the IEEE 118-bus and WECC 240-bus cases
- **bes\_neighbors.py** lists the adjacent buses and connecting branches for each bus in the system
- **clean.bat** removes temporary output files on Windows
- **clean.sh** removes temporary output files on Linux and Mac OS X
- **grid\_upgrades.py** summarizes the saved HCA results from a *out.json* file, and suggests branch upgrades to increase hosting capacity
- **hca.py** call the HCA function, as configured by a JSON file name supplied as the first command-line argument
- **hca\_prep.py** reads a Matpower base case file, outputs the *wmva.m* with branch ratings and *\_prep.json* file with contingencies and buses for hosting capacity analysis.
- **IEEE118.m** defines the IEEE 118-bus base case for Matpower
- **IEEE118\_Network.json** defines the network layout for plotting; file comes from CIMHub
- **IEEE188\_out.json** saved HCA results with N-1 contingencies
- **IEEE118\_prep.json** defines the buses, branch contingencies, grid upgrades and load scaling for hosting capacity analysis of the IEEE 118-bus test system.  Overwritten by *hca\_prep.py*
- **IEEE118\_wmva.m** base case with branch MVA ratings. Overwritten by *hca\_prep.py*
- **matpower\_gen\_type.m** Matpower support function identifying solar and wind generators from type codes PV and WT. Not currently used.
- **most.py** solves MOST base case for IEEE 118-bus (default, or argument=0) or WECC 240-bus test system (argument=1).
- **mpow.py** solves Matpower AC power flow base case for IEEE 118-bus (default, or argument=0) or WECC 240-bus test system (argument=1).
- **plot\_bes.py** plots the network layout of the bulk electric system for IEEE 118-bus test system (default, or argument=0) or the WECC 240-bus test system (argument=1)
- **plot\_hca.py** plots the bus hosting capacity and branch congestion levels on a network layout
- **set\_softlims.m** utility script to enable soft limits in the HCA solution
- **test\_118.json** configures load scaling, buses of interest, grid upgrades, and branch contingencies for hosting capacity analysis for a 1-bus test case on the IEEE 118-bus system
- **test\_240.json** configures load scaling, buses of interest, grid upgrades, and branch contingencies for hosting capacity analysis for a 1-bus test case on the WECC 240-bus system
- **test\_solver.json** configures GLPK options for attempting to solve HCA at bus 103 of the WECC240 system, including a 230/20 kV transformer contingency.
- **WECC240.m** defines the WECC 240-bus base case for Matpower
- **WECC240\_Network.json** defines the network layout for plotting; file comes from CIMHub
- **WECC240\_out.json** saved HCA results with N-1 contingencies
- **WECC240\_prep.json** defines the buses, branch contingencies, grid upgrades and load scaling for hosting capacity analysis of the WECC 240-bus test system.  Overwritten by *hca\_prep.py*
- **WECC240\_wmva.m** base case with branch MVA ratings. Overwritten by *hca\_prep.py*

Also, see the **tests/** sub-directory for 3-day unit commitment and hosting
capacity test cases on an 8-bus model of the ERCOT test system used for
the Distribution System Operation with Transactive (DSO+T) study.

## N-1 Contingency Selection

The current logic for selecting contingencies at each bus is based on:

- A few branches with highest MVA ratings in the whole system. This is the same for each candidate bus. Currently:
    - The IEEE 118-bus system has 11 contingencies, for branches rated 400 MVA or higher
    - The WECC 240-bus system has 5 contingencies, for branches rated 5000 MVA or higher
- At each candidate bus, the branches to each adjacent bus are included in a set of contingencies. This set varies with bus location. Currently:
    - The IEEE 118-bus system has up to 12 local bus-based contingencies, or up to 23 total per HCA case.
    - The WECC 240-bus system has up to 9 local bus-based contingencies, or up to 14 total per HCA case.
- For each type of contingency, branches with MVA or kV ratings below 100 are excluded. This excludes generator step-up and load-serving transformers, although these can still be limiting branches.

## Sample Results - IEEE118

To run HCA on the IEEE 118-bus test system, configured with N-1 contingencies:

- **python hca\_prep.py 0**
- Full N-1 HCA: **python hca.py IEEE118\_prep.json**
- Faster 1-bus test case: **python hca.py test\_118.json**

The following analysis of 118 buses took 1082 seconds to run on the 
IEEE118 system.  Results are saved to *IEEE118\_out.json* after each bus 
analysis, in case one of them fails to converge with iterations that don't 
terminate in Octave.

To summarize actionable results from this IEEE118 HCA analysis, based on 
the results stored in *IEEE118\_out.json*: 

- **python grid\_upgrades.py 0**

This produces two sections of output.  The first several lines of each 
section are shown below.  The first section shows the summary of hosting 
capacity at each bus, and the total generation dispatch by fuel type (*ng* 
is natural gas, while *dl* is dispatchable load, which is not included in 
these models.) HCA dispatch is achieved for these four buses by reducing 
natural gas dispatch.  The second section of output summarizes branch 
upgrade suggestions, based on the shadow prices, *muF*.  

```
 Bus   Generation by Fuel [MW]
          hca     wind    solar  nuclear    hydro     coal       ng       dl  [Max muF Branch] [Mean muF Branch]
   1    34.41   428.80  1364.40     0.00     0.00     0.00  1034.89     0.00
   2    13.50   428.80  1364.40     0.00     0.00     0.00  1055.81     0.00
   3   183.32   428.80  1364.40     0.00     0.00     0.00   885.98     0.00  [44.5000 on 68] [3.1786 on 68]
   4    26.32   428.80  1364.40     0.00     0.00     0.00  1042.98     0.00  [44.0000 on 177] [3.3846 on 177]


Branch Upgrade Suggestions:
 Bus   HC[MW]
   1    34.41
   2    13.50
   3   183.32
       Max Mu Branch:   68 (  44.500) Line   3- 12  138.00 kV x=0.1600, z=378.06 ohms, npar=1, mva=157.00, mi=38.09
      Mean Mu Branch:   68 (   3.179) Line   3- 12  138.00 kV x=0.1600, z=378.06 ohms, npar=1, mva=157.00, mi=38.09
   4    26.32
       Max Mu Branch:  177 (  44.000) Xfmr 104-183  138.00 /   13.80 kV x=0.0536, mva=186.40
      Mean Mu Branch:  177 (   3.385) Xfmr 104-183  138.00 /   13.80 kV x=0.0536, mva=186.40
```

The branch shadow prices are too low from the HCA on buses 1 and 2 to 
identify the limiting branch.  At bus 3, the hosting capacity is 183.32 
MW.  To increase this limit, *muF* suggests that the single-circuit 138-kV 
line between buses 3 and 12 might be upgraded.  For example, a second line 
of the same impedance and MVA rating might be constructed in parallel.  At 
bus 4, the hosting capacity is 26.32 MW.  To increase that limit, 
upgrading the 138/13.8 kV transformer between buses 104 and 183 might be 
upgraded.  For example, a second 186-MVA transformer might be added in 
parallel.  

In reviewing the entire output:

- The hosting capacity is zero at 7 buses, i.e., 12, 26, 63, 71, 85, 87, and 111. At some of these buses, e.g., 12, the N-1 contingency analysis results in curtailing the existing wind and solar generation all the way to zero. This indicates a possible need for reinforcing the base system.
- There are some buses, e.g, 23, where non-zero hosting capacity is achieved by curtailing nearby wind and solar generation, not just natural gas.

## Sample Results - WECC240

To run HCA on the WECC 240-bus test system, at 187 candidate buses 
configured with N-1 contingencies: 

- **python hca\_prep.py 1**
- Full N-1 HCA: **python hca.py WECC240\_prep.json &**
- Faster 1-bus test case: **python hca.py test\_240.json**

Solution time was 6640 seconds and the results are saved to 
*WECC240\_out.json*.  To summarize actionable results from this WECC240 
HCA analysis, based on the saved results: 

- **python grid\_upgrades.py 1**

Interpretation of this output was discussed in the previous section.  The 
hosting capacity is zero at 28 buses: 2, 20, 41, 58, 59, 81, 123, 124, 
125, 126, 127, 128, 129, 163, 164, 172, 173, 174, 175, 176, 177, 178, 179, 
187, 200, 206, 227, 233 

It was not possible to determine an accurate total solution time, because 
the HCA failed on bus 24.  To work around that failure, this procedure was 
followed: 

- Unlike the IEEE 118-bus system, solve the WECC 240-bus system with Python running in the **background**, i.e, using the **&** operator.
- After displaying results for bus 22, the HCA fails to make any visible progress for several minutes.
- Use **ps** to find the process running **octave-cli** and use **kill -9 ####** to stop that process.
    - The supervising Python process should indicate that HCA solution failed, and proceed to the next one.
    - Subsequent HCA bus results should be saved in the *WECC240\_out.json* file.

Possible improvements may come from reinforcing the base model, revising 
the logic for contingency selection, or adding GLPK solution options.  The 
*test\_solver.json* file has been set up for exploring the GLPK options at 
a selected bus in the WECC240 system.  It should be modified to focus on 
bus 24, or another bus of current interest, instead of bus 103.  

## Allowable Number of Contingencies

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

The solution times were obtained in a Ubuntu Virtual Machine (UVM), 
allocated up to 8 GB RAM. The CPU speed was benchmarked according to: 

- *sudo apt-get install sysbench*
- *sysbench cpu run*
- resulting CPU speed is **1071.62** events per second

The *Bus 1 Hosting Capacity* results in this section include only 
size-based contingencies, not the local bus-based contingencies as 
described in the following section.  As a result, the hosting capacity 
results given above are too optimistic.  However, the solution times vs.  
total number of contingencies are still valid.  

## Incorporating Local Contingencies

In these system models, branches with highest MVA ratings often represent 
two or more lines and transformers in parallel.  A N-1 contingency means 
removing only one of these paralleled branches, so the entire equivalent 
branch is not removed from service, only reduced in rating and increased 
in impedance.  These rating-reduction contingencies may not be limiting 
the hosting capacity at different buses.  To obtain more realistic 
results, we supplement the rating-based list with a bus-based list, which 
changes at each candidate bus during HCA.  The bus-based contingencies 
include the set of branches to immediately adjacent buses.  When these 
local branches represent more than one line or transformer in parallel, 
only one of those is removed from service.  
 
In the IEEE118 system, the size-based contingencies include 11 branches 
rated 400 MVA or more, plus up to 12 bus-based contingencies. Bus 117 is 
radial, with no parallel branch connections. Its hosting capacity would be 
zero under N-1 conditions, except for serving local load at bus 117. 

In the WECC240 system, the size-based contingencies include 5 branches 
rated 5000 MVA or more, plus up to 9 bus-based contingencies. Buses 40 and 
82 are radial, with no parallel branch connections. 

## Simulating Interconnection Queues

Instead of performing HCA over all candidate buses, the interconnection 
queue simulation could be done one project at a time, representing the 
order of projects in a queue. The steps for each new project in a 
conventional queue would be: 

- Run *hca\_prep.py* to build contingency lists and generator tables based on a current state of the system.
- Prune the *hca\_buses* array in the resulting *\_prep.json* to include only the bus of interest. It's possible to run HCA on many buses at this point, but the extra results become invalid whenever a new project is connected to the grid.
- Run *hca.py* on the modified *\_prep.json* file to obtain hosting capacity and grid upgrade estimates.
    - If the hosting capacity is less than the project size, there will be no grid upgrade cost.
    - Otherwise, add branches to the system and re-run the process from *hca\_prep.py* until the hosting capacity is large enough.
        - Estimate the cost of these upgrades from the total line length or transformer MVA added, adjusting the cost for voltage level.
        - Add these upgrades to the base model. If existing branches are upgraded, these can be included as *upgrades* in the *_prep.json* file. Brand new branches need to be added to the original *.m* file; there are no existing helper scripts for that task.
- As each project is connected to the grid, it should be added to the original *.m* file; there are no existing helper scripts for that task.

The steps for an auction-based process would be:

- Run *hca\_prep.py* to build contingency lists and generator tables based on a current state of the system.
- Run *hca.py* over all candidate buses.
    - If the total system-wide hosting capacity isn't high enough to satisfy resource requirements, add grid upgrades and re-run from the *hca\_prep.py* stage. The cost of these upgrades may be recovered through a minimum bid for interconnecting projects.
- Define the minimum bids and maximum allowed capacity for each bus to be included in the auction.
    - Run a confirming N-1 analysis for a system with a set of auctioned projects connected to the grid. The purpose is to verify feasibility of interconnecting a set of auction-winning projects to the grid. However, there are no existing helper scripts for this task.

## Example of Queue and Auction Simulations

From the *./tests* subdirectory:

- **python impact.py**

produces the following results:

```
***********************************************
Auction Process on buses [6, 3, 8]
Generation by Fuel[GW]
    hca    wind   solar nuclear   hydro    coal      ng      dl
  9.648  14.391   0.000   5.139   0.000  21.566  15.341   0.000
 Bus    HC [MW]
   6   4552.694
   3   3855.826
   8   1239.512
Merit order of upgrades:
 Br# From   To     muF      MVA      kV  Add MVA    Miles  Cost $M
   1    5    6  4.8935  2168.00  345.00  1084.00   142.43   508.49
  13    1    3  4.1832  3252.00  345.00  1084.00   212.56   753.96
   4    1    2  4.0474  2168.00  345.00  1084.00   207.00   734.49
   8    6    7  3.5878  2168.00  345.00  1084.00   199.86   709.52
   7    4    8  1.7354  2168.00  345.00  1084.00   214.74   761.59
   9    2    5  0.3557  6504.00  345.00  1084.00   148.51   529.78
  11    3    4  0.0190  2168.00  345.00  1084.00   147.63   526.71
***********************************************
Queue Process on 3 applications
Processing application for 5000.00 MW at bus 6
  Added 5000.00 MW solar at bus 6 for $0.000M
Processing application for 4400.00 MW at bus 3
  HC=4122.50 MW, upgrade branch 1 by 1.5000 at $508.489M
  IX Cost $508.489M is too high, HC=4422.132 MW
Processing application for 2000.00 MW at bus 8
  HC=1239.51 MW, upgrade branch 1 by 1.5000 at $508.489M
  HC=1239.51 MW, upgrade branch 7 by 1.5000 at $761.593M
  Added 2000.00 MW wind at bus 8 for $1270.082M
```

In the 8-bus ERCOT model, buses 3, 6, and 8 have the lowest hosting 
capacity. The auction simulation indicates that 9648 MW can be hosted 
among those three buses, without any system upgrades. A queue simulation 
results in 7 GW actually connected to the system, but one applicant had to 
pay $1270M in system upgrade costs. Because the project at bus 6 came 
first in the queue, that project was able to connect 5000 MW, which is 
higher than 4553 MW allocated to that bus for an auction. Nothing was 
connected at bus 3 because the applicant was unwilling to pay $508M in 
grid upgrade costs. However, a smaller project might have been accepted at 
bus 3. The last project at bus 8 was able to connect 2000 MW, which is 
higher than the auction limit at bus 8, but only by paying for grid 
upgrades.
 
In the queue process, an upgrade on branch 1 was proposed for the project 
at bus 3, but not added to the grid because the project withdrew. Later, 
the project at bus 8 paid for the same proposed upgrade on branch 1, in 
addition to an upgrade on branch 7. The sizes, locations, and upgrade cost 
limits are configurable for each application in the Python script. 

## Simulating Interconnection Queues on Medium-Scale Systems

For the IEEE 118-bus system:

```
C:\src\i2x\bes>python bq_simulations.py 0 3
Auction Bus List [ 52  30 115 107  41]
System IEEE118_wmva.m, Req MW=[150.00,400.00], Max $M/MW=[0.10,0.30], Nauc=5, Ncls=5, Napp=10
***********************************************
Auction Process on IEEE118_wmva.m, POC buses=[ 52  30 115 107  41]
AUCTION RESULTS
Generation by Fuel[GW]
    hca    wind   solar nuclear   hydro    coal      ng      dl
  1.267   0.361   1.234   0.000   0.000   0.000   0.000   0.000
 Bus    HC [MW]
  52    169.146
  30    553.698
 115    171.846
 107    190.740
  41    181.968
Merit order of upgrades:
 Br# From   To     muF      MVA      kV  Add MVA    Miles  Cost $M
 204   30   17  0.0433   257.73  345.00   800.00 Xfmr        12.20
  72   41   42  0.0267   157.00  138.00   157.00    32.14    68.27
  93   52   53  0.0256   157.00  138.00   157.00    38.92    81.84
  11  105  107  0.0251   157.00  138.00   157.00    43.56    91.13
  48   27  115  0.0231   157.00  138.00   157.00    17.64    39.28
 195   19  130  0.0054    49.60  138.00   200.00 Xfmr         3.20
 191   15  126  0.0051    53.60  138.00   200.00 Xfmr         3.20
 206   31  138  0.0024    62.00  138.00   200.00 Xfmr         3.20
 219   54  149  0.0018   105.60  138.00   200.00 Xfmr         3.20
 221   55  151  0.0018    12.00  138.00   200.00 Xfmr         3.20
 177  104  183  0.0013   186.40  138.00   200.00 Xfmr         3.20
 179  105  185  0.0013   108.80  138.00   200.00 Xfmr         3.20
 173  100  179  0.0013    41.60  138.00   200.00 Xfmr         3.20
 174  100  180  0.0013   160.00  138.00   200.00 Xfmr         3.20
 253   92  175  0.0013   207.60  138.00   200.00 Xfmr         3.20
 244   82  168  0.0013   139.20  138.00   200.00 Xfmr         3.20
 233   69  159  0.0012    49.60  138.00   200.00 Xfmr         3.20
 240   76  165  0.0010    10.00  138.00   200.00 Xfmr         3.20
***********************************************
Queue Process on 3 bus application cluster(s) for IEEE118_wmva.m
Processing application for 914.86 MW at bus 115
  HC=171.85 MW, upgrade branch 48 by 2.0000 at $39.279M
  HC=325.78 MW, upgrade branch 32 by 2.0000 at $78.414M
Processing application for 681.58 MW at bus 41
  HC=181.97 MW, upgrade branch 32 by 2.0000 at $78.414M
  HC=181.97 MW, upgrade branch 72 by 2.0000 at $68.273M
Processing application for 1413.79 MW at bus 30
  HC=552.85 MW, upgrade branch 204 by 4.1040 at $12.200M
  HC=623.36 MW, upgrade branch 28 by 2.0000 at $63.227M
APPLICATION CLUSTERS
 Bus   Req [MW]  MaxCost $M  Itlim  #apps
 115     914.86      111.07     2     3
         347.40       42.44     2
         331.60       38.17     2
         235.86       30.45     2
  41     681.58      113.66     2     3
         230.41       30.78     2
         194.25       24.30     2
         256.92       58.58     2
  30    1413.79      236.76     2     4
         342.56       99.53     2
         336.67       49.07     2
         376.80       38.93     2
         357.76       49.23     2
CLUSTER STUDY RESULTS
 Bus   Req [MW]  Add [MW]   HC [MW]   Cost $M   Branch Upgrades
 115     914.86      0.00    325.78    117.69   [48, 32]
  41     681.58      0.00    181.97    146.69   [32, 72]
  30    1413.79      0.00    623.36     75.43   [204, 28]
77.67 seconds elapsed
```

For the WECC 240-bus system:

```
C:\src\i2x\bes>python bq_simulations.py 1 4
Auction Bus List [112 225  20   7 150]
System WECC240_wmva.m, Req MW=[200.00,1000.00], Max $M/MW=[0.10,0.30], Nauc=5, Ncls=5, Napp=10
***********************************************
Auction Process on WECC240_wmva.m, POC buses=[112 225  20   7 150]

AUCTION RESULTS
Generation by Fuel[GW]
    hca    wind   solar nuclear   hydro    coal      ng      dl
 18.451  20.039  34.120   4.210  38.435   0.000  25.043   0.000
 Bus    HC [MW]
 112   1642.016
 225   7319.623
  20    600.000
   7   7548.477
 150   1340.467
Merit order of upgrades:
 Br# From   To     muF      MVA      kV  Add MVA    Miles  Cost $M
 393  112  218 14.6532   334.45  115.00   100.00 Xfmr         2.45
 442  222  231 11.1031  1000.00  345.00   800.00 Xfmr        12.20
 406  134  151  7.8665   750.00  500.00  1200.00 Xfmr        24.40
 445  226  227  4.8732   512.82  345.00   800.00 Xfmr        12.20
 189  134  135  3.4328  1800.00  500.00  1800.00    14.42    77.67
 347   33   24  2.8018   724.64  500.00  1200.00 Xfmr        24.40
 336    7    8  2.7388   684.93  500.00  1200.00 Xfmr        24.40
   9    7   18  2.7277  1800.00  500.00  1800.00    87.92   371.67
  70   57  225  2.3228  1084.00  345.00  1084.00    48.60   180.11
 252  180  182  2.0952  1800.00  500.00  1800.00    83.33   353.33
 426  193  194  1.6766  1000.00  500.00  1200.00 Xfmr        24.40
 433  204  206  1.5947   552.49  500.00  1200.00 Xfmr        24.40
 245  167  168  1.3686   600.00  230.00   600.00     0.77     7.61
 436  211  213  1.1675   552.49  345.00   800.00 Xfmr        12.20
   3    2    4  0.9348  1084.00  345.00  1084.00    10.51    46.80
  28   22   31  0.7445   600.00  230.00   600.00    35.70    80.97
 341   14   15  0.2753  1388.89  500.00  1200.00 Xfmr        24.40
  26   20   24  0.0681   600.00  230.00   600.00    46.51   103.68
 407  135  150  0.0226   574.71  500.00  1200.00 Xfmr        24.40
 380   83   85  0.0068   334.45  230.00   400.00 Xfmr         5.80
***********************************************
Queue Process on 4 bus application cluster(s) for WECC240_wmva.m
Processing application for 2801.61 MW at bus 112
  HC=1811.44 MW, upgrade branch 252 by 2.0000 at $353.333M
  HC=1767.67 MW, upgrade branch 393 by 1.2990 at $2.450M
Processing application for 2462.42 MW at bus 7
  Added 2462.42 MW solar at bus 7 for $0.000M
Processing application for 244.55 MW at bus 20
  HC=149.00 MW, upgrade branch 252 by 2.0000 at $353.333M
  HC=71.21 MW, upgrade branch 307 by 1.5000 at $252.315M
Processing application for 970.00 MW at bus 150
  Added 970.00 MW wind at bus 150 for $0.000M
APPLICATION CLUSTERS
 Bus   Req [MW]  MaxCost $M  Itlim  #apps
 112    2801.61      483.82     2     4
         847.58       88.29     2
         750.33       93.95     2
         276.44       50.74     2
         927.26      250.84     2
   7    2462.42      585.98     2     3
         897.26      217.56     2
         573.43       98.45     2
         991.73      269.97     2
  20     244.55       36.28     2     1
 150     970.00      150.47     2     2
         525.17       90.76     2
         444.83       59.72     2
CLUSTER STUDY RESULTS
 Bus   Req [MW]  Add [MW]   HC [MW]   Cost $M   Branch Upgrades
 112    2801.61      0.00   1767.67    355.78   [252, 393]
   7    2462.42   2462.42   7548.48      0.00   None
  20     244.55      0.00     71.21    605.65   [252, 307]
 150     970.00    970.00    990.89      0.00   None
221.27 seconds elapsed
```

For the IEEE 39-bus system:

```
C:\src\i2x\bes>python bq_simulations.py 2 2
System IEEE39_wmva.m, Req MW=[500.00,500.00], Max $M/MW=[0.20,0.20], Nauc=6, Ncls=6, Napp=3
***********************************************
Auction Process on IEEE39_wmva.m, POC buses=[10, 11, 12, 13, 14, 15]

AUCTION RESULTS
Generation by Fuel[GW]
    hca    wind   solar nuclear   hydro    coal      ng      dl
  1.232   0.000   0.000   0.865   0.870   0.000   3.287   0.000
 Bus    HC [MW]
  10      0.000
  11    488.530
  12      0.000
  13      0.000
  14      0.000
  15    743.595
Merit order of upgrades:
 Br# From   To     muF      MVA      kV  Add MVA    Miles  Cost $M
   9    4   14  6.5547   500.00  345.00  1084.00    25.59    99.57
   3    2    3  5.5480   500.00  345.00  1084.00    29.95   114.84
  13    6   11  1.6699   480.00  345.00  1084.00    16.27    66.93
***********************************************
Queue Process on 2 bus application cluster(s) for IEEE39_wmva.m
Processing application for 1000.00 MW at bus 10
  HC=586.42 MW, upgrade branch 3 by 3.1680 at $114.841M
  HC=564.35 MW, upgrade branch 13 by 3.2583 at $66.934M
Processing application for 500.00 MW at bus 13
  HC=488.53 MW, upgrade branch 3 by 3.1680 at $114.841M
  HC=488.53 MW, upgrade branch 13 by 3.2583 at $66.934M

APPLICATION CLUSTERS
 Bus   Req [MW]  MaxCost $M  Itlim  #apps
  10    1000.00      200.00     2     2
         500.00      100.00     2
         500.00      100.00     2
  13     500.00      100.00     2     1
CLUSTER STUDY RESULTS
 Bus   Req [MW]  Add [MW]   HC [MW]   Cost $M   Branch Upgrades
  10    1000.00      0.00    564.35    181.77   [3, 13]
  13     500.00      0.00    488.53    181.77   [3, 13]
16.67 seconds elapsed
```


Copyright 2022-2023, Battelle Memorial Institute

