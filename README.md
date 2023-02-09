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

Some other important notes about the program:

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


### Examples: Low-Voltage Secondary Network

## Developers

The steps for deployment to PyPi are:

1. `rm -rf dist`
2. `python -m build`
3. `twine check dist/*` should not show any errors
4. `twine upload -r testpypi dist/*` requires project credentials for i2x on test.pypi.org
5. `pip install -i https://test.pypi.org/simple/ i2x==0.0.2` for local testing of the deployable package, example version 0.0.2
6. `twine upload dist/*` final deployment; requires project credentials for i2x on pypi.org

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
