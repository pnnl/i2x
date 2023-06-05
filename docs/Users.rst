i2x Tool Users
==============

The i2x DER package has been tested on Windows only, with Python 3.10.  It 
does net yet support Mac OS X or Linux.  During the installation process, 
a version of OpenDSS will be installed to work with the Python interface, 
i.e., you do not have to install OpenDSS separately.  The steps are: 

1. Install Python 3 if necessary. This is available from `Python Site <https://python.org>`_, 
   `Anaconda/Miniconda <https://www.anaconda.com/>`_, or the 
   `Microsoft Store <https://apps.microsoft.com/store/detail/python-310/9PJPW5LDXLZ5>`_.
2. On the second panel of Python 3's installer, select the option that
   adds Python variables to your system environment, which includes the **path**.
3. From a command prompt [#f1]_, `pip install i2x --upgrade`

Once installed, invoke the GUI from a command prompt: `i2x-der`

Sources of background information include:

1. Slides from the first DER interconnection study boot camp by 
   `PNNL <_static/DER_Bootcamp_Circuits.pdf>`_, 
   `NRECA <_static/NRECA_Bootcamp%20slides_v2.pdf>`_ and 
   `GridUnity <_static/GU_GridTech_Connect_DER_Interconnection_Study_Bootcamp.pdf>`_.
2. `CIGRE Canada Paper <https://cigre.ca/papers/2021/paper%20460.pdf>`_ on hosting 
   capacity analysis methods, focused on North America.
3. `Multi-country Survey of Hosting Capacity <https://www.mdpi.com/1996-1073/13/18/4756>`_

DER GUI Reference
-----------------

When you start the program, six tabbed pages appear in a notebook format:

1.  **Network** shows an overview map of the circuit selected from a library.  Buses are labeled when they have either a substation source, or DER at least 100 kW in size.  X and Y coordinates are arbitrary.  You can pan and zoom this map using the toolbar, but can not modify it or obtain more data from it.  A key to the legend is: 

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

2. **DER** summarizes DER and load on the circuit. **kVA** refers to the size, while **kW** refers to the requested output. The **Available Residential Rooftops** include single-phase load points without existing DER, with 120/240-volt service. You can choose a percentage of these to populate with new PV each time a case is run. The size at each location depends on local load:

   - The PV size matches the local load size, rounded to the nearest 5 kW.
   - When the rounded PV size is 0 kW, the minimum size is 3 kW instead.

   The rooftop locations change each time due to randomization, which usually produces a slight variation when you repeat a case, unless you set the useage rate to 0%. You can change the **kW**, **kvar**, and even the **type** of existing large DER, but you can't add new large DER at a different location. You can effectively remove DER by setting **kW** to 0.

3. **Solar** offers a choice of time-dependent solar output profiles, which apply to each PV in the circuit.
4. **Loads** offers a choice of time-dependent load output profiles, which apply to each load in the circuit. You can also apply a global scaling factor to the loads, which acts along with the load profile.
5. **Inverters** offers a choice of 7 inverter functions that respond to voltage, which apply uniformly to every PV and storage inverter in the circuit. Please see IEEE 1547 and its application guides for more details. The **Power Factor** applies to both **CONSTANT\_PF** and **VOLT\_WATT** modes. Enter a negative number to absorb reactive power, positive to inject reactive power. In other modes, the red curve shows how reactive power varies in response to voltage.
6. **Output** allows you to run a simulation and view the results. Click the blue **Run** button to run a new case. The other widgets on this page are:

   - **Solution Mode** should be **DAILY** for a 24-hour simulation using the **pcloud** or **pclear** solar profile. Use **DUTY** with the **pvduty** solar profile to focus on rapid voltage regulator and capacitor switching response. Less often, use **SNAPSHOT** to run a single power flow, with limited results shown.
   - **Control Mode** should be **STATIC**. Change this only if you are familiar with how it works in OpenDSS.
   - **Stop Time** specifies how long a period will be simulated. 1440 minutes covers one day, while 48 minutes covers the **pvduty** solar profile.
   - **Time Step** specifies the period between each power flow solution. There is a tradeoff between precision of the voltage fluctuations, and the simulation time. The software requires a value from 1 to 300, inclusive.
   - **Output PV Details** will show the production and voltage results for each PV in the circuit. There may be a lot of these, especially on residential roof tops.
   - **Clear Old Output** will erase prior results before displaying new ones. This is the default, so new results appear right at the top whenever you run a new case. If you unselect this option, please remember to scroll down to the bottom of the results each time you run a new case. The advantage is that you will now have a log of all cases run. Use copy-and-paste to another program to save any of these results.
   - **Summary Results** is a row of labels that will show in **red** when important limits are violated in the simulation results. See below for more details.
   - **Detailed Results** appear in the large white area below the other widgets, categorized as follows:

     - **Number of Capacitor Switchings**: the number of times a capacitor bank switched on or off. Expect no more than 2 per capacitor bank per day. If higher, PV fluctuations may be the cause.
     - **Number of Tap Changes**: the total number of voltage regulator tap movements. Expect one or two dozen per day per regulator. If higher, PV fluctuations may be the cause.
     - **Number of Relay Trips**: if not zero, PV reverse power flow may be the cause. Any time a relay trips, some load has likely lost service. Furthermore, the following voltage and energy results may be unreliable. When this is not zero, the DER hosting capacity limit has been exceeded.
     - **Nodes with Low Final Voltage**: how many node voltages at the last time point fell below the ANSI C84.1 A Range, i.e., 0.95 perunit. *Minimum PV Voltage* is more significant because it considers all time points.
     - **Nodes with High Final Voltage**: how many node voltages at the last time point fell above the ANSI C84.1 A Range, i.e., 1.05 perunit. *Maximum PV Voltage* is more significant because it considers all time points.
     - **Load Served**: total energy delivered to loads in the circuit
     - **Substation Energy**: total energy from the substation, i.e., the bulk electric system
     - **Losses**: total losses in lines and transformers
     - **Generation**: total energy from conventional generation
     - **Solar Output**: total real power production from PV
     - **Solar Reactive Energy**: total reactive power production from PV, in response to local voltage
     - **Energy Exceeding Normal**: EEN is an estimate of the load energy delivered under conditions of voltage outside normal limits, and/or conditions of line or transformer current above normal limits. This may indicate the need for grid infrastructure upgrades. It indicates that a DER hosting capacity limit has been exceeded. See the OpenDSS documentation for more details.
     - **Unserved Energy**: UE is defined like EEN, but with emergency limits rather than normal limits. Load would not be disconnected, but non-zero UE is a stronger indication that grid upgrades are needed, that DER hosting capacity has been exceeded, and that operational problems are more likely.
     - **Minimum PV Voltage**: among all PV and times, in per-unit. 
     - **Maximum PV Voltage**: among all PV and times, in per-unit.
     - **Maximum PV Voltage Change**: the voltage change, in percent, is measured as the largest difference in PV voltage magnitude between consecutive time points. There is some sensitivity to the choice of **Time Step**. In more detailed OpenDSS modeling, signal processing techniques are applied to mitigate the sensitivity, but for illustrative purposes in the **i2x-der** software, that's not necessary. The voltage change, **Vdiff**, should be limited to 2% or 3%, depending on the local electric utility guidelines. Otherwise, nearby customers may complain. The **Vdiff** results consider only the PV locations, as the load **Vdiff** values should all be equal to or less than the worst PV value. The use of inverter control modes could mitigate **Vdiff** without having to reduce the amount of DER.
     - **PV Details**: if requested, shows the real and reactive energies, and the voltage results, for each PV in the model.

   - **Check for Updates** will compare your installed software version to the latest on PyPi. Requires an Internet connection.

Some other important notes about the program:

- The main window is resizable. The graphs and the output results display may increase in size.
- Close the program by clicking the **X** in the top right corner.
- As you run simulations, some logging messages appear in the Command Prompt. You don't need to pay attention to these, unless an error occurs. If there is an error message, please copy-and-paste the message into your issue report.
- Please report any comments, suggestions, or errors on the `issues page <https://github.com/pnnl/i2x/issues>`_. Before submitting a new issue, check the others listed to see if the problem or suggestion has already been reported.  If it has, you might still add new information to the existing issue as a comment. The issues page is better than emailing for this purpose, as it helps the team organize these reports and updates. It also creates a public record that may help other users.

DER Example: 9500-Node Network
------------------------------

When you first start **i2x-der**, the `IEEE 9500 node circuit <https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-33471.pdf>`_ is displayed. We can use this to examine the effect of inverter controls on solar-induced voltage fluctuations:

- Go to the **DER** tab, and reduce the usage of residential rooftops to 0%. This makes the results repeatable.
- Go the the **Output** tab and run a case. You should find the maximum PV voltage fluctuation to be at or near 0.7552%. This is less than 2%, and should be acceptable, but that's on a clear day.
- Go to the **Solar** tab and select the **pcloud** profile. The graph shows much more variation in output. Use this profile for the rest of the example. If you run the case again, the voltage fluctuation should exceed 3%, which is not acceptable.
- Go to the **Inverters** tab and try non-unity power factors, e.g., 0.9153 and -0.9153. One of these improves the voltage fluctuation, while one makes it worse. Both choices result in significant levels of PV reactive energy. In IEEE Standard 1547-2018, the minimum power factor required of Category B inverters is 0.9153, so these two results bound the reactive power injection of inverters operating at constant power factor.
- On the **Inverters** tab, try the **VOLT\_WATT** function, which is designed to mitigate steady-state voltage rise. It doesn't affect the voltage fluctuations in this case, i.e., you should get approximately the same result as you did with the same power factor in **CONSTANT\_PF** mode. The IEEE 9500-node circuit doesn't have significant voltage rise problems, even if you were to add much more PV.
- On the **Inverters** tab, try the other functions. Results are tabulated below.

  - **VOLT\_VAR\_CATA** has a small beneficial effect, but it's not very aggressive in using reactive power. 
  - **VOLT\_VAR\_CATB** is more aggressive, but only outside a "deadband" of zero response (see its graph). In this case, the voltage fluctuations occur mostly within the deadband, which spans 4%.
  - **VOLT\_VAR\_AVR** uses the most aggressive response allowed in IEEE 1547-2018, along with "autonomously adjusting reference voltage" as described on page 39 of IEEE 1547-2018. There is no deadband, but the setpoint is not fixed at 1 perunit reference voltage. Instead, the **VOLT\_VAR\_CATB** setpoint follows the grid voltage with a response time of several minutes. The effect is to resist sudden voltage changes, while not resisting longer term changes in grid voltage. In this case, it reduces the voltage fluctuation below 2%, and the PV reactive energy is only 0.55% of the PV real energy. There are higher short-term transients in PV reactive power, but over the day these net to nearly zero. On the other hand, the **CONSTANT\_PF** result with -0.9153 power factor also reduced the voltage fluctuation below 2%, but the PV reactive energy was 44.0% of the PV real energy, i.e., the PV absorbed reactive power all the time.
  - **VOLT\_VAR\_VOLT\_WATT** uses both **VOLT\_VAR\_CATB** and **VOLT\_WATT**, at unity power factor. Because of the deadband, it doesn't help with voltage fluctuations in this case.
  - **VOLT\_VAR\_14H** uses both volt-var and volt-watt characteristics according to Hawaii Rule 14H, which was developed for an area that has high steady-state voltage rise on some long secondary circuits. The volt-watt characteristic is more aggressive, but the volt-var characteristic has a wider deadband, of 6%. As a result, it helps even less with voltage fluctuations in this case.
  - Although not illustrated here, **VOLT\_VAR\_AVR** may be combined with **VOLT\_WATT** to address steady-state voltage rise along with voltage fluctuations. This is the same combination in IEEE 1547-2018 that allows the **VOLT\_VAR\_VOLT\_WATT** and **VOLT\_VAR\_14H** modes.

======= ====================== ======= ==================================================
Profile Inverters              Vdiff   Notes
======= ====================== ======= ==================================================
pclear  CONSTANT\_PF=1.0       0.7552  No problem on a clear day.
pcloud  CONSTANT\_PF=1.0       3.2108  With clouds, too much voltage fluctuation.
pcloud  CONSTANT\_PF=0.9153    4.5894  Injecting reactive power makes it worse.
pcloud  CONSTANT\_PF=-0.9153   1.8005  Absorbing reactive power all the time.
pcloud  VOLT\_WATT, PF=-0.9153 1.8006  Similar to CONSTANT\_PF at same power factor.
pcloud  VOLT\_VAR\_CATA        2.9250  Helps a little.
pcloud  VOLT\_VAR\_CATB        3.1626  No help in the deadband.
pcloud  VOLT\_VAR\_AVR         1.6010  Setpoint adjusts to grid voltage in a few minutes.
pcloud  VOLT\_VAR\_VOLT\_WATT  3.1626  Still no help in the deadband.
pcloud  VOLT\_VAR\_14H         3.2090  Still no help in the deadband.
======= ====================== ======= ==================================================

Suggested exercises for this circuit:

- Add more residential rooftop PV without exceeding the hosting capacity.
- Use the **pvduty** solar profile to explore the effects of inverter control mode on regulator tap changes.
- Use the **DER** tab to replace as much of the conventional generation as possible with PV. How could you quantify the effect on local air quality?
- Use the **DER** tab to increase the existing **pvfarm1** size as much as possible.

DER Example: Low-Voltage Secondary Network
------------------------------------------

The second available circuit is an `IEEE Low-Voltage Network Test System <https://doi.org/10.1109/PESGM.2014.6939794>`_. It comprises 8 radial primary feeders that supply a grid of 480-V and 208-V secondary cables in an urban, downtown area. This design provides economic, high-reliability service to dense load areas, but it does not support very much DER. The network protectors (NWP) trip on reverse power flow, as intended for faults on a primary feeder. DER can also cause NWP trips under normal conditions, which is not intended. To explore this effect:

- On the **Network** tab, select **ieee\_lvn** and review the locations of NWP with respect to the primary feeders and the secondary grid. There are 8 fixed PV locations indicated in yellow. In a dense urban area like this, there are no available residential rooftops for single-phase PV.
- On the **DER** tab, the PV are dispatched to a total of 800 kW, which is only 1.9% of the peak load. IEEE 1547.6-2011, which is an application guide for DER on secondary network systems, refers to such a limit as "de minimus".
- On the **Output** tab, run the case. There should be no voltage problems because of the strong grid, and no relay trips because of the "de minimus" quantity of DER.
- On the **DER** tab, change each DER to dispatch at 1000 kW, as might have been intended for 1095 kva ratings. This is still only 19% of the peak load.
- On the **Output** tab, run the case again. Now, you should see 4 relay trips, and some of the loads are unserved. Two of the eight PV were also disconnected. This result is not acceptable.
- On the **DER** tab, adjust the individual DER kW and kva parameters to achieve as high a hosting capacity as possible.
- Some changes to the traditional NWP scheme have been investigated to increase the DER hosting capacity, but these are advanced topics and not considered in the **i2x-der** software.

.. rubric:: Footnotes

.. [#f1] On Windows 10, this may be found from the **Start Menu** under **Windows System / Command Prompt**. On Windows 11, one method is to search for **Command Prompt** from the **Start Button**. Another method is to find **Terminal** under **All apps** from the **Start Button**.
