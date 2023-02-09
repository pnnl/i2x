# Interconnection Innovation e-Xchange (i2x) Open Test Systems 

This repository contains open grid network models and modeling scripts to 
test and compare different factors/measures (e.g., technoeconomic, social, 
equity, and engineering) that examine practices and policies for 
interconnection queue management and cost allocation.  This repository is 
used for engineering training bootcamps, interconnection study guides, and 
an interconnection roadmap for the [i2x project](https://energy.gov/i2x).  

## Users

The i2x DER package has been tested on Windows only, with Python 3.10.  It 
does net yet support Mac OS X or Linux.  During the installation process, 
a version of OpenDSS will be installed to work with the Python interface, 
i.e., you do not have to install OpenDSS separately.  The steps are: 

1. Install Python 3 if necessary. This is available from [Python Site](https://python.org), [Anaconda/Miniconda](https://www.anaconda.com/), or the [Microsoft Store](https://apps.microsoft.com/store/detail/python-310/9PJPW5LDXLZ5).
2. On the second panel of Python 3's installer, select the option that adds Python variables to your system environment, which includes the _path_.
3. From a command prompt[^1], `pip install i2x --upgrade`

Once installed, invoke the GUI from a command prompt[^1]: `i2x-der`

### User Interface

When you start the program, six tabbed pages appear in a notebook format:

1. **Network** shows an overview map of the circuit selected from a library.
   Buses are labeled when they have either a substation source, or DER at
   least 100 kW in size. X and Y coordinates are arbitrary.  You can pan and
   zoom this map using the toolbar, but can not modify it or obtain more data
   from it.  A key to the legend is:
   - LN = line segment
   - XFM = transformer segment
   - REG = voltage regulator segment
   - SWT = switch segment
   - NWP = network protector segment
   - RCT = series reactor segment
   - SUB = substation
   - GEN = (conventional) generator
   - PV = photovoltaic generator
   - CAP = capacitor bank
   - BAT = battery, i.e., storage
2. **DER** summarizes DER and load on the circuit. _kVA_ refers to the size,
   while _kW_ refers to the requested output. The _Available Residential Rooftops_
   include single-phase load points without existing DER, with 120/240-volt service.
   You can choose a percentage of these to populate with new PV each time a case
   is run. The size at each location depends on local load:
   - The PV size matches the local load size, rounded to the nearest 5 kW.
   - When the rounded PV size is 0 kW, the minimum size is 3 kW instead.
   The rooftop locations change each time due to randomization, which usually produces a slight
   variation when you repeat a case, unless you set the useage rate to 0%. You can change
   the _kW_, _kvar_, and even the _type_ of existing large DER, but you can't add new
   large DER at a different location. You can effectively remove DER by setting _kW_ to 0.
3. **Solar** offers a choice of time-dependent solar output profiles, which apply to
   each PV in the circuit.
4. **Loads** offers a choice of time-dependent load output profiles, which apply to
   each load in the circuit. You can also apply a global scaling factor to the loads, which
   acts along with the load profile.
5. **Inverters** offers a choice of 7 inverter functions that respond to voltage, which apply
   uniformly to every PV and storage inverter in the circuit. Please see IEEE 1547 and its
   application guides for more details. The _Power Factor_ applies to both _CONSTANT\_PF_ and
   _VOLT\_WATT_ modes. Enter a negative number to absorb reactive power, positive to inject
   reactive power. In other modes, the red curve shows how reactive power varies in response
   to voltage.
6. **Output** allows you to run a simulation and view the results. Click the blue **Run** button
   to run a new case. The other widgets on this page are:
   - _Solution Mode_ should be _DAILY_ for a 24-hour simulation using the _pcloud_ or _pclear_ 
     solar profile. Use _DUTY_ with the _pvduty_ solar profile to focus on rapid voltage regulator
     and capacitor switching response. Less often, use _SNAPSHOT_ to run a single power flow, with
     limited results shown.
   - _Control Mode_ should be _STATIC_. Change this only if you are familiar with how it works
     in OpenDSS.
   - _Stop Time_ specifies how long a period will be simulated. 1440 minutes covers one day, while
     48 minutes covers the _pvduty_ solar profile.
   - _Time Step_ specifies the period between each power flow solution. There is a tradeoff between
     precision of the voltage fluctuations, and the simulation time. The software requires a value
     from 1 to 300, inclusive.
   - _Output PV Details_ will show the production and voltage results for each PV in the circuit.
     There may be a lot of these, especially on residential roof tops.
   - _Clear Old Output_ will erase prior results before displaying new ones. This is the default, so
     new results appear right at the top whenever you run a new case. If you unselect this option,
     please remember to scroll down to the bottom of the results each time you run a new case. The
     advantage is that you will now have a log of all cases run. Use copy-and-paste to another program
     to save any of these results.
   - _Results_ appear in the large white area below the other widgets, categorized as follows:
     - _Number of Capacitor Switchings_: the number of times a capacitor bank switched on or off. Expect no more than 2 per capacitor bank per day. If higher, PV fluctuations may be the cause.
     - _Number of Tap Changes_: the total number of voltage regulator tap movements. Expect one or two dozen per day per regulator. If higher, PV fluctuations may be the cause.
     - _Number of Relay Trips_: if not zero, PV reverse power flow may be the cause. Any time a relay trips, some load has likely lost service. Furthermore, the following voltage and energy results may be unreliable. 
       When this is not zero, the DER hosting capacity limit has been exceeded.
     - _Nodes with Low Voltage_: how many node voltages fell below the ANSI C84.1 A Range, i.e., 0.95 perunit
     - _Nodes with High Voltage_: how many node voltages fell above the ANSI C84.1 A Range, i.e., 1.05 perunit 
     - _Load Served_: total energy delivered to loads in the circuit
     - _Substation Energy_: total energy from the substation, i.e., the bulk electric system
     - _Losses_: total losses in lines and transformers
     - _Generation_: total energy from conventional generation
     - _Solar Output_: total real power production from PV
     - _Solar Reactive Energy_: total reactive power production from PV, in response to local voltage
     - _Energy Exceeding Normal_: EEN is an estimate of the load energy delivered under conditions of voltage outside normal limits,
       and/or conditions of line or transformer current above normal limits. This may indicate the need for grid infrastructure
       upgrades. It indicates that a DER hosting capacity limit has been exceeded. See the OpenDSS documentation for more details.
     - _Unserved Energy_: UE is defined like EEN, but with emergency limits rather than normal limits. Load would not
       be disconnected, but non-zero UE is a stronger indication that grid upgrades are needed, that DER hosting capacity has been
       exceeded, and that operational problems are more likely.
     - _Minimum PV Voltage_: among all PV, in per-unit. 
     - _Maximum PV Voltage_: among all PV, in per-unit.
     - _Maximum PV Voltage Change_: the voltage change, in percent, is measured as the largest difference in PV voltage magnitude
       between consecutive time points. There is some sensitivity to the choice of _Time Step_. In more detailed OpenDSS
       modeling, signal processing techniques are applied to mitigate the sensitivity, but for illustrative purposes in the _i2x-der_
       software, that's not necessary. The voltage change, _Vdiff_, should be limited to 2% or 3%, depending on the local electric
       utility guidelines. Otherwise, nearby customers may complain. The _Vdiff_ results consider only the PV locations, as the
       load _Vdiff_ values should all be equal to or less than the worst PV value. The use of inverter control modes could
       mitigate _Vdiff_ without having to reduce the amount of DER.
     - _PV Details_: if requested, shows the real and reactive energies, and the voltage results, for each PV in the model.

Some other important notes about the program:

- The main window is resizable. The graphs and the output results display may increase in size.
- Close the program by clicking the **X** in the top right corner.
- As you run simulations, some logging messages appear in the Command Prompt. You don't
  need to pay attention to these, unless an error occurs. If there is an error message,
  please copy-and-paste the message into your issue report.
- Please report any comments, suggestions, or errors on the [issues page](https://github.com/pnnl/i2x/issues).
  Before submitting a new issue, check the others listed to see if the problem or suggestion
  has already been reported.  If it has, you might still add new information to the existing
  issue as a comment. The issues page is better than emailing for this purpose, as it helps 
  the team organize these reports and updates. It also creates a public record that may help
  other users.

### Examples: 9500-Node Network

When you first start _i2x-der_, the [IEEE 9500 node circuit](https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-33471.pdf) is displayed.
We can use this to examine the effect of inverter controls on solar-induced voltage fluctuations:

- Go to the **DER** tab, and reduce the usage of residential rooftops to 0%. This
  makes the results repeatable.
- Go the the **Output** tab and run a case. You should find the maximum PV voltage fluctuation
  to be at or near 0.8656%. This is less than 2%, and should be acceptable, but that's on a clear day.
- Go to the **Solar** tab and select the **pcloud** profile. The graph shows much more variation
  in output. Use this profile for the rest of the example. If you run the case again, the
  voltage fluctuation should exceed 3%, which is not acceptable.
- Go to the **Inverters** tab and try non-unity power factors, e.g., 0.9 and -0.9. One of these
  improves the voltage fluctuation, while one makes it worse. Both choices result in significant
  levels of PV reactive energy.
- On the **Inverters** tab, try the _VOLT\_WATT_ function, which is designed to mitigate steady-state
  voltage rise. It doesn't affect the voltage fluctuations in this case, i.e., you should get approximately
  the same result as you did with the same power factor in _CONSTANT\_PF_ mode. The IEEE 9500-node
  circuit doesn't have significant voltage rise problems, even if you were to add much more PV.
- On the **Inverters** tab, try the other functions. Results are tabulated below.
  - _VOLT\_VAR\_CATA_ has a small beneficial effect, but it's not very aggressive in using reactive power. 
  - _VOLT\_VAR\_CATB_ is more aggressive, but only outside a "deadband" of zero response 
    (see its graph). In this case, the voltage fluctuations occur mostly within the deadband, which spans 4%.
  - _VOLT\_VAR\_AVR_ uses the most aggressive response allowed in IEEE 1547-2018, along with "autonomously
    adjusting reference voltage" as described on page 39 of IEEE 1547-2018. There is no deadband, but the
    setpoint is not fixed at 1 perunit reference voltage. Instead, the se_VOLT\_VAR\_CATB_ point follows the grid voltage with 
    a response time of several minutes. The effect is to resist sudden voltage changes, while not resisting
    longer term changes in grid voltage. In this case, it reduces the voltage fluctuation below 2%, and the
    PV reactive energy is only 0.80% of the PV real energy. There are higher short-term transients in PV reactive
    power, but over the day these net to nearly zero. On the other hand, the _CONSTANT\_PF_ result with -0.9
    power factor also reduced the voltage fluctuation below 2%, but the PV reactive energy was 48.4% of the PV
    real energy, i.e., the PV absorbed reactive power all the time.
  - _VOLT\_VAR\_VOLT\_WATT_ uses both _VOLT\_VAR\_CATB_ and _VOLT\_WATT_, at unity power factor. Because of the
    deadband, it doesn't help with voltage fluctuations in this case.
  - _VOLT\_VAR\_14H_ uses both volt-var and volt-watt characteristics according to Hawaii Rule 14H, which was
    developed for an area that has high steady-state voltage rise on some long secondary circuits. The volt-watt
    characteristic is more aggressive, but the volt-var characteristic has a wider deadband, of 6%. As a result,
    it helps even less with voltage fluctuations in this case.
  - Although not illustrated here, _VOLT\_VAR\_AVR_ may be combined with _VOLT\_WATT_ to address steady-state
    voltage rise along with voltage fluctuations. This is the same combination in IEEE 1547-2018 that allows
    the _VOLT\_VAR\_VOLT\_WATT_ and _VOLT\_VAR\_14H_ modes.

| Profile | Inverters | Max Vdiff [%] | Notes |
| ------- | --------- | -----: | ------------|
| pclear | CONSTANT\_PF=1.0 | 0.8656 | No problem on a clear day. |
| pcloud | CONSTANT\_PF=1.0 | 3.1382 | With clouds, too much voltage fluctuation. |
| pcloud | CONSTANT\_PF=0.9 | 4.5609 | Injecting reactive power makes it worse. |
| pcloud | CONSTANT\_PF=-0.9 | 1.6858 | Absorbing reactive power all the time. |
| pcloud | VOLT\_WATT, PF=-0.9 | 1.6999 | Close to CONSTANT\_PF result at same power factor. |
| pcloud | VOLT\_VAR\_CATA | 2.8752 | Helps a little. |
| pcloud | VOLT\_VAR\_CATB | 3.0721 | No help in the deadband. |
| pcloud | VOLT\_VAR\_AVR | 1.5747 | Setpoint adjusts to grid voltage over several minutes. |
| pcloud | VOLT\_VAR\_VOLT\_WATT | 3.0721 | Still no help in the deadband. |
| pcloud | VOLT\_VAR\_14H | 3.1209 | Still no help in the deadband. |

Suggested exercises for this circuit:

- Add more residential rooftop PV without exceeding the hosting capacity.
- Use the _pvduty_ solar profile to explore the effects of inverter control mode on regulator tap changes.
- Use the **DER** tab to replace as much of the conventional generation as possible with PV. How could you
  quantify the effect on local air quality?
- Use the **DER** tab to increase the existing _pvfarm1_ size as much as possible.

### Examples: Low-Voltage Secondary Network

The second available circuit is an [IEEE Low-Voltage Network Test System](https://doi.org/10.1109/PESGM.2014.6939794).
It comprises 8 radial primary feeders that supply a grid of 480-V and 208-V secondary cables in an urban, downtown area.
This design provides economic, high-reliability service to dense load areas, but it does not support very much DER.
The network protectors (NWP) trip on reverse power flow, as intended for faults on a primary feeder. DER can also cause
NWP trips under normal conditions, which is not intended. To explore this effect:

- On the **Network** tab, select _ieee\_lvn_ and review the locations of NWP with respect to the primary feeders and
  the secondary grid. There are 8 fixed PV locations indicated in yellow. In a dense urban area like this, there are
  no available residential rooftops for single-phase PV.
- On the **DER** tab, the PV are dispatched to a total of 800 kW, which is only 1.9% of the peak load. IEEE 1547.6-2011,
  which is an application guide for DER on secondary network systems, refers to such a limit as "de minimus".
- On the **Output** tab, run the case. There should be no voltage problems because of the strong grid, and no relay trips
  because of the "de minimus" quantity of DER.
- On the **DER** tab, change each DER to dispatch at 1000 kW, as might have been intended for 1095 kva ratings. This is
  still only 19% of the peak load.
- On the **Output** tab, run the case again. Now, you should see 4 relay trips, and some of the loads are unserved. Two
  of the eight PV were also disconnected. This result is not acceptable.
- On the **DER** tab, adjust the individual DER kW and kva parameters to achieve as high a hosting capacity as possible.
- Some changes to the traditional NWP scheme have been investigated to increase the DER hosting capacity, but these
  are advanced topics and not considered in the _i2x-der_ software.

## Developers

Familiarity with `git` and Python is expected.  Experience with OpenDSS is 
also helpful.  The steps for working on the i2x Python code are: 

1. From your local directory of software projects: `git clone https://github.com/pnnl/i2x.git`
2. `cd i2x`
3. `pip install -e .` to install i2x from your local copy of the code.

The steps for deployment to PyPi are:

1. `rm -rf dist`
2. `python -m build`
3. `twine check dist/*` should not show any errors
4. `twine upload -r testpypi dist/*` requires project credentials for i2x on test.pypi.org
5. `pip install -i https://test.pypi.org/simple/ i2x==0.0.8` for local testing of the deployable package, example version 0.0.8
6. `twine upload dist/*` final deployment; requires project credentials for i2x on pypi.org

## Bulk Electric System (BES) Test Cases

Two BES test systems are under development at [CIMHub/BES](https://github.com/GRIDAPPSD/CIMHub/tree/feature/SETO/BES).
These will be used in BES boot camps and i2x sprint studies.

## License

See [License](license.txt)

## Notice

This material was prepared as an account of work sponsored by an agency of the United States Government.  Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any of their employees, nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe privately owned rights.
Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.

    PACIFIC NORTHWEST NATIONAL LABORATORY
                operated by
                 BATTELLE
                 for the
     UNITED STATES DEPARTMENT OF ENERGY
      under Contract DE-AC05-76RL01830

Copyright 2022-2023, Battelle Memorial Institute

[^1]: On Windows 10, this may be found from the _Start Menu_ under _Windows System / Command Prompt_. On Windows 11, one method is to search for _Command Prompt_ from the _Start Button_. Another method is to find _Terminal_ under _All apps_ from the _Start Button_.
