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

Copyright 2022-2023, Battelle Memorial Institute

