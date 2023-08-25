# Bulk Electric System (BES) Analysis for i2x 

This repository contains Matpower scripts for BES hosting
capacity analysis, used in sprint studies for the i2x roadmap.
Prerequisites include: 
 
- [Octave 8.2](https://octave.org/download). MATLAB could also work, but Octave is free, has a smaller footprint, and includes the GLPK solver.

- [Matpower 7.1](https://matpower.org/). Install and test in Octave as directed, choosing option 3 to save the Matpower paths within Octave.

The test systems are based on [CIMHub/BES](https://github.com/GRIDAPPSD/CIMHub/blob/feature/SETO/BES). To run a simulation in Matpower or MOST:

- `python mpow.py [#]` where **#** is 0 for the IEEE 118-bus case, or 1 for the WECC 240-bus case, defaults to 0. Produces output in txt files.
- `python most.py [#]` where **#** is 0 for the IEEE 118-bus case, or 1 for the WECC 240-bus case, defaults to 0. Produces output in txt files.

## Directory of Script and Data Files

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
- **test\_118.json** configures load scaling, buses of interest, grid upgrades, and branch contingencies for hosting capacity analysis for a 1-bus test case on the IEEE 118-bus system
- **test\_240.json** configures load scaling, buses of interest, grid upgrades, and branch contingencies for hosting capacity analysis for a 1-bus test case on the WECC 240-bus system
- **WECC240.m** defines the WECC 240-bus base case for Matpower
- **WECC240\_Network.json** defines the network layout for plotting; file comes from CIMHub
- **WECC240\_out.json** saved HCA results with N-1 contingencies
- **WECC240\_prep.json** defines the buses, branch contingencies, grid upgrades and load scaling for hosting capacity analysis of the WECC 240-bus test system.  Overwritten by *hca\_prep.py*
- **WECC240\_wmva.m** base case with branch MVA ratings. Overwritten by *hca\_prep.py*

Also, see the **tests/** sub-directory for 3-day unit commitment and hosting
capacity test cases on an 8-bus model of the ERCOT test system used for
the Distribution System Operation with Transactive (DSO+T) study.

## Sample Results - IEEE118

To run HCA on the IEEE 118-bus test system, configured with N-1 contingencies:

- **python hca\_prep.py 0**
- Full N-1 HCA: **python hca.py IEEE118\_prep.json**
- Faster 1-bus test case: **python hca.py test\_118.json**

The following simulation took a few minutes to run on the IEEE118 system. Results
are saved to *IEEE118\_out.json* after each bus analysis, in case one of them
fails to converge with iterations that don't terminate in Octave.

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

To run HCA on the WECC 240-bus test system, configured with N-1 contingencies:

- **python hca\_prep.py 1**
- Full N-1 HCA: **python hca.py WECC240\_prep.json**
- Faster 1-bus test case: **python hca.py test\_240.json**

The HCA analysis of 187 buses with two N-1 contingencies took 17 
minutes to run on the WECC240 system. Results are saved to 
*WECC240\_out.json*. At buses 67 and 226, the hosting capacity is zero.

To summarize actionable results from this WECC240 HCA analysis:

- **python grid\_upgrades.py 1**

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

The solution times were obtained in a Ubuntu Virtual Machine (UVM), 
allocated up to 8 GB RAM. The CPU speed was benchmarked according to: 

- *sudo apt-get install sysbench*
- *sysbench cpu run*
- resulting CPU speed is **1071.62** events per second

## Incorporating Local Contingencies

In these system models, branches with highest MVA ratings often represent 
two or more lines and transformers in parallel. A N-1 contingency means 
removing only one of these paralleled branches, so the entire equivalent 
branch is not removed from service, only reduced in rating and increased 
in impedance. These rating-reduction contingencies may not be limiting 
hosting capacity at different buses. To obtain more realistic results, we 
supplement the rating-based list with a bus-based list, which changes at 
each candidate bus during HCA. The bus-based contingencies include the set 
of branches to immediately adjacent buses. When these local branches 
represent more than one line or transformer in parallel, only one of those 
is removed from service.
 
In the IEEE118 system, the size-based contingencies include 11 branches 
rated 400 MVA or more, plus up to 12 bus-based contingencies. Bus 117 is 
radial, with no parallel branch connections. Its hosting capacity would be 
zero under N-1 conditions, except for serving local load at bus 117. The 
HCA simulation took 1285 seconds in the UVM. At many buses with low 
hosting capacity, *muF* was apparently too small for identifying any 
limiting branches. 

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
        - Estimate the cost of these upgrades from the total line length or transformer MVA added, adjusting for voltage level.
        - Add these upgrades to the base model. If existing branches are upgraded, these can be included as *upgrades* in the *_prep.json* file. Brand new branches need to be added to the original *.m* file; there are no existing helper scripts for that task.
- As each project is connected to the grid, it should be added to the original *.m* file; there are no existing helper scripts for that task.

The steps for an auction-based process would be:

- Run *hca\_prep.py* to build contingency lists and generator tables based on a current state of the system.
- Run *hca.py* over all candidate buses.
    - If the total system-wide hosting capacity isn't high enough to satisfy resource requirements, add grid upgrades and re-run from the *hca\_prep.py* stage. The cost of these upgrades may be recovered through a minimum bid for projects.
- Define the minimum bids and maximum allowed capacity for each bus to be included in the auction.
    - Run a confirming N-1 analysis for a system with a set of auctioned projects connected to the grid, but there are no existing helper scripts for this task.

Copyright 2022-2023, Battelle Memorial Institute

