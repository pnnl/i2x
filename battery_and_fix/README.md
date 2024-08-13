# Battery Usage with Flexible Interconnection
* [BESS Optimization Model](#model)
* [Solar Profiles](#solar-profiles)
* [Running the model](#running-the-model)
* [Installation](#installation)

## Model
### Parameters
| Parameter | Description |
| :----- | :---------  |
| $f$ | Hourly Generation forecast |
| $hc$ | Hourly hosting capacity |
| $g_{\text{over}} = f - \min(f, hc)$| Over generation for each hour |
| $c_{\text{energy}}$| Hourly energy price |
| $r_{\text{kW}}$ | Battery Kilowatt rating|
| $r_{\text{kWh}}$| Battery Kilowatt-hour rating |

### Variables
| Variable | Domain | Description |
| :-----  | :-----:| :---------  |
| $b_{\text{charge}}$ | $[0, r_{\text{kW}}]$ | Battery charging |
| $b_{\text{discharge}}$ | $[0, r_{\text{kW}}]$| Battery discharging |
| $b_{\text{nogen, charge}}$ |  | Battery charging **not** from over generation|
| $E$ | $[0, r_{kWh}]$ | Battery state of charge |
| $c$ | $\geq 0$ | Curtailment |
| $u$ | $\{0,1\}$ | 1 if battery discharging, 0 if charging |

### Objective
Objective is to maximize battery discharge while minimizing cost from charging the battery during _non-over-generation_ periods:
$$
\underset{b}{\text{maximize}} \sum_{t} c_{\text{energy}}\left(b_{\text{discharge}}[t] - b_{\text{nogen, charge}}\right)
$$

### Constraints
#### Curtailment
The curtailment is _at worst_ equal to the over generation:
$$
c[t] \leq g_{\text{over}}[t]
$$

#### Output
The total output which is the curtailment adjusted forecast plus battery behavior must be below the hosting capacity:
$$
b_{\text{discharge}}[t] - b_{\text{charge}}[t] + f[t] - c[t] \leq hc[t]
$$

#### Charging from over generation
total bess charging minus charging from non-over-generation solar plus curtailment
must be equal to the the total over generation. 

$$
b_{\text{charging}}[t] - b_{\text{nogen, charge}}[t] + c[t] = g_{\text{over}}
$$

Consider the following cases:
* Case 1: no over-generation $g_{\text{over}} = 0$
  * curtailment is 0 due to the curtailment constraint
  * all charging is not from over generation ($b_{\text{nogen, charge}}=b_{\text{charging}}$)
* Case 2: some over-generation $g_{\text{over}} > 0$
  * curtailment is 0 (assumption)
  * total charge is reduced by over generation to equal charging from not over-generation ($b_{\text{nogen, charge}}=b_{\text{charging}} - g_{\text{over}}$)
* Case 3: some over-generation $g_{\text{over}} > 0$
  * curtailment is not 0 (assumption)
  * any remaining overhead is reduced from total charge to yield charge not from over-generation ($b_{\text{nogen, charge}}=b_{\text{charging}} - (g_{\text{over}} - c)$)

#### Net Output
The net output of battery and generation cannot go negative (i.e. only charging is not allowed):
$$
f[t] - b_{\text{charging}}[t] >= 0
$$

#### Charge/Discharge Selection
Charge and discharge are indicated using variable $u$
$$
b_{\text{charging}}[t] \leq r_{\text{kW}}\cdot (1-u[t])
$$

$$
b_{\text{discharge}}[t] \leq r_{\text{kW}}\cdot u[t]
$$

#### Battery State of Charge
The state of charge changes from hour to hour according to (assumption is 1 hour intervals):
$$
E[t] = E[t-1] - b_{\text{discharge}}[t] + b_{\text{charge}}
$$



## Inadvertent Export
The inadvertent export screen recommended by the BATRIES toolkit as follows:
$$
\frac{R_{sc} \Delta P - X_{sc} \Delta Q}{V^2} \leq 0.03
$$
Where $R_{sc}$ and $X_{sc}$ are the Thevenin impedances at the bus of interest, and $\Delta P$ and $\Delta Q$ are the difference between nameplate and export limit, with
$$
\Delta P = (S_{r} - S_{HC})\times PF\\
\Delta Q = (S_{r} - S_{HC})\times \sqrt{1 - PF^2}
$$
where $S_{r}$ is the rated MVA, $S_{HC}$ the hosting capacity/export limit and $PF$ the power factor.

This can be solved $(S_{r} - S_{HC})$ to get the maximum size _beyond_ the export limit that the DER can be without leading to Rapid Voltage Change (RVC) issues:
$$
(S_{r} - S_{HC}) [kVA] = 0.03 \times \frac{(V[kV])^2}{R_{sc} [\Omega]\cdot PF - X_{sc}[\Omega]\cdot \sqrt{1 - PF^2}}\times 1000
$$
Under the assumption of $PF=1$ this becomes:
$$
\Delta P_{max} = ({P_r} - P_{HC}) [kW] = 30 \times \frac{(V[kV])^2}{R_{sc} [\Omega]\cdot PF}
$$

There are two ways to think about this limit:
1) the maximum rating is $\min(P_{HC}) + \Delta P_{max}$. This way the nameplate is _never_ above the maximum rating.
2) consider a unitized solar shape and find the scalar that keeps it no more than $\Delta P_{max}$ above the hosting capacity for all hours:
$$
\begin{align*}
&\text{Maximize} \quad&& c\\
&\text{subject to}\quad&& c\cdot f_{pu}[t] - hc[t] \leq \Delta P_{max}\quad \forall t\in \end{align*}
$$
## Solar Profiles
The solar profiles are based on data from the NTP project that was created by NREL's ReVX tool.
The profile is based on a location close to the Hoosick Substation.
Any other profile could be use however.

## Running the model
The main program is in [`bessopt.py`](./bessopt.py), help is accessible via
```
>python bessopt.py --help
usage: bessopt.py [-h] [--print-hca-stats] configfile

Solve for optimal BESS utilization given solar profile and hosting capacity results

positional arguments:
  configfile         .toml configuration

options:
  -h, --help         show this help message and exit
  --print-hca-stats  print hca statistics and exit.
```

if the `--print-hca-stats` flag is set the statistics of the profile and hosting capacity data will be displayed.
This is useful for coming up with with possible battery sizes, or experimenting with different scaling of the solar projects.

## Limited Generation Profiles
The hosting capacity used so far is made up of a unique value per hour.
This might be too optimistic of an assumption as far as data availability goes.
Instead, we can generate the three different limited generation profiles from the hourly data as described in the [recent CA ruling](https://docs.cpuc.ca.gov/PublishedDocs/Published/G000/M527/K828/527828730.PDF) (see pg. 71-72) that describes 3 different profiles with 24 unique values for the year.

### Steps Overview
1. Set up the configuration file to point to the correct data (have `f_scale=1`)
2. Run `python bessopt.py <config file> --print-hca-stats` to get a sense of the statistics.
3. Get the the short circuit impedance by running `python hca_zsc.py --bus <bus>` (in [test](../test/hca_zsc.py) and currently fixed to the 9500 node model, so for other models, some modification will be needed). Updated config with results.
4. Calculate maximum capacity given RVC limits via `python bessopt.py <config file> --rvc-lim`
5. Select capacity of DER and Battery
6. Run the optimization

### Configuration Options
The following configuration options are available
#### System Data
| Parameter | Req./Opt. [default]| Description |
| :------- | :----------------|:------------|
| `bes_kw`  | **required** | Battery max charge/discharge in kW |
| `bes_kwh` | **required** | Battery capacity in kWh |
| `hc`      | **required** | array of hosting capacity values OR path to csv/excel file with 
| `hc_scale`  | optional [1] | scaling factor for `hc` array data|
| `hc_col`  | **required** (if not array) | column name in hc file with hc data|
| `hc_index_col`| optional [0] | index column in hc file|
| `hc_sheet_name`| **required** (if Excel) | sheet name in Excel book with hc data|
| `f`       | **required** | array of solar profile values OR path to csv/excel with data|
| `f_scale`  | **required** | scaling factor for `f` array data |
| `f_col`  | **required** (if not array) | column name in profile file with profile data|
| `f_index_col`| optional [0] | index column in profile file|
| `f_sheet_name`| **required** (if Excel) | sheet name in Excel book with profile data|

#### Market Data
| Parameter | Req./Opt. [default]| Description |
| :------- | :----------------|:------------|
| `energy_price`| **required** | Path to csv or Excel with price data (8760) |
| `energy_price_col`| **required** | Name of column with values to use as the energy price |
| `dvr_price_col` | **required**| column with demand value reduction prices (used for benefit calculation) |
| `energy_price_index_col`| optional [0] | Index column when reading the data |
| `energy_price_sheet_name`| **required** (if Excel) | sheet name in Excel book |
| `dvr_adjust` | **required** | path to csv or Excel with adjustment factors (over 25 years) for the DVR price |
| `dvr_adjust_col`| **required**| Name of column where the adjustment factors are located|
| `dvr_adjust_index_col` | optional [0] | Index column for DVR data |
| `dvr_adjust_sheet_name` | **required** (if Excel) | sheet name for DVR data in Excel book |

#### CAPEX Data
| Parameter | Req./Opt. [default]| Description |
| :------- | :----------------|:------------|
| `capex_years`| **required** (max 25) | Years over which costs and benefits are evaluated (anything other than 25 may require some adjustments) |
| `der_dollar_per_kw`| **required** | Cost of DER in $/kW |
| `der_om_dollar_per_kw_year`| **required** | DER O&M costs in $/kW-y |
| `bess_dollar_per_kw_year`| **required**| Battery cost in $/kW |
| `bess_om_dollar_per_kw_year`| **required** | Battery O&M Costs in $/kW-y|
| `bess_inverter_fraction`| optional [0] (< 1) | Fraction to reduce Battery investment due to shared inverter with DER |
| `degredation` | **required** | equipment performance degradation factor |
| `escalation` | **required** | price escalation factor |
| `discout_rate`| **required** | capital discount rate |

#### Program Controls
| Parameter | Req./Opt. [default]| Description |
| :------- | :----------------|:------------|
| `study_year`| optional [current year] | just used for creating time indices|
| `savename`| optional [`bessopt.xlsx] | Excel file to save the optimization results to|
| `run_no_fix`| optional [False] | If True a scenario with solar equal to the minimum HC without battery is performed |
| `copy_price_data`| optional [False] | If True the energy price and dvr scale data will be copied to output |
| `solver` | optional [cbc] | Solver to pass to the pyomo model|
| `plot`| optional | parameters from yearly results to plot, in addition "NPV" can be specified|
| `plot_path`| optional [current directory] | Directory to store plot files |

#### RVC Analysis
| Parameter | Req./Opt. [default]| Description |
| :------- | :----------------|:------------|
|`rsc`| **required** (only for `--rvc-lim` option) | short circuit resistance [Ohm] |
|`xsc`| **required** (only for `--rvc-lim` option) | short circuit reactance [Ohm] |
|`kvbase_ll` | **required** (only for `--rvc-lim` option) | voltage base in kV |
| `pf` | optional [1] | Power factor |
| `rvc_limit` | optional [0.03] | the RVC limits |


### Outputs
The output excel file is structured as follows:
* Sheet _fixed_ with columns:
    - _forecast_: the input profile forecast (scaling applied)
    - _HC_: the input hosting capacity profile (scaling applied)
    - _output\_no\_bess_: output without any battery (forecast - curtailment without BESS)
    - _curtailment\_no\_bess_: curtailment without battery (forecast - min(forecast, hc))
* Sheet _variables_ with columns:
    - _bess_: kW charge (-) discharge (+) time series of the battery
    - _E_: kWh state of charge time series of the battery
    - _output_: kW net export from PV + BESS (this is forecast + bess - curtailment)
    - _curtailment_: kW curtailment (this is forecast + bess - min(forecast + bess, hc))
* Sheet _no\_fix_ (only if `run_no_fix = True`) with columns:
    - _forecast_: input profile scaled to the minimum hosting capacity
    - _HC_: the input hosting capacity profile
    - _curtailment_: Any curtailment, should be all zeros.
    - _output_: forecast minus curtailment, should be identical to forecast.
* Sheet _configuration_ with the input configuration. Includes the no fix capacity if `run_no_fix=True`.

## Installation
The model is built using [pyomo](https://www.pyomo.org/).
To run it the following installation steps are necessary:
### Install pyomo 
```
conda install -c conda-forge pyomo
```
Check version using:
```
>pyomo --version
Pyomo 6.7.2 (CPython 3.10.12 on Windows 10)
```
(output may be different)

### Installing CBC on Windows
Cbc installation appears to be not very supported on windows.
The following appears to work for getting the installation working.

#### Python environment
For this example a `conda` environment is assumed (something like `conda create --name i2x`).
There are other ways to work with python environments, with some modification potentially necessary.

#### Get the Binaries
The CBC binaries can be downloaded from [here](https://www.coin-or.org/download/binary/Cbc/?C=M;O=D).
Download one for win64.

This will download a zip file to your computer. For example:
```
Cbc-master-win64-msvc15-mtd.zip
```

Extract the zip files.

Under the created folder structure navigate to `bin`

There should be three `.exe` files located there:
* `cbc.exe`
* `clp.exe`
* `glpsol.exe`

#### Copy to Python Environment

The three `.exe` binaries need to now be copied to the `bin` folder of your Python environment.
This should be located at:
```
<Your-Anacond/Minicond-Installation-Folder>/envs/<environment-name>/Library/bin
```
### Install ipopt
There appears to be an issue with ipopt versions `>3.11` that the `ipopt.exe` is no longer included when installing (at least via conda).
See [this issue](https://github.com/conda-forge/ipopt-feedstock/issues/55).
As a result, if ipopt, say version 3.14 (latest at the time of writing) is used, then pyomo (which requires the `ipopt.exe` binary apparently) errors, stating that the application could not be found.

A solution to this is to install version 3.11:
```
conda install ipopt=3.11 -c conda-forge
```
Check version using:
```
ipopt --version
Ipopt 3.11.1 (Microsoft cl 16.00.40219.01 for x64), ASL(20130606)
```
(output may be different)

Check that pyomo can see ipopt using
```
pyomo help --solvers
```