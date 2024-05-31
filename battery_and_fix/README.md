# Battery Usage with Flexible Interconnection
* [BESS Optimization Model](#model)
* [Solar Profiles](#solar-profiles)
* [Running the model](#running-the-model)
* [Installation](#installation)
## Model
The model assumes that there is a der (e.g. solar) generation profile, $f[t]$ and a hosting capacity profile $hc[t]$.

The curtailment, $c$ in general would be:
$$
c[t] = f[t] - \min(f[t], hc[t])
$$

The objective of the model is to maximize charging (minimize negative injection) during hours where curtailment would occur, $c[t] > 0$:
$$
\underset{b}{\text{minimize}} \sum_{t\in T_c} b[t]
$$
where $b[t]$ is the battery charge/discharge (-/+) behavior in kW at time $t$, and $T_c = \{t: c[t] > 0\}$, the set of all times where curtailment _would_ happen.

The following constraints apply:
### Power and Energy limits
The battery has specified charge/discharge rate limits:
$$
-P_{\text{lim}} \leq b[t] \leq P_{\text{lim}}\quad \forall t\in T
$$

The battery has a specified capacity:
$$
0 \leq E[t] \leq E_{\text{max}} \quad \forall t \in T
$$
where $E[t]$ is the state of charge of the battery in kWh at time $t$.

### State of Charge Dynamic
The state of charge changes from hour to hour according to (assumption is 1 hour intervals):
$$
E[t] = E[t-1] + b[t]
$$

### No Grid Charging
We do not let the battery charge from the grid by forcing the net output (forecast plus batter) to always be greater than or equal to zero.
$$
f[t] + b[t] \geq 0 \quad \forall t \in T
$$

### Hosting Capacity Limit When Discharging
When the default curtailment _would_ be zero, the battery output should not push the net output beyond the hosting capacity limit:
$$
f[t] + b[t] \leq hc[t] \quad \forall t \in T\setminus T_c
$$
where $T\setminus T_c$ is the set of all hours where there is no curtailment.
Note that for hours where there _is_ curtailment ($t\in T_c$) the battery output not going be positive (discharging) since that runs counter to the objective function.

## Solar Profiles
The solar profiles are based on data from the NTP project that was created by NREL's ReVX tool.
The profile is based on a location close to the Hoosick Substation.
Any other profile could be use however.

## Running the model
The main program in in [`bessopt.py`](./bessopt.py), help is accessible via
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

### Configuration Options
The following configuration options are available
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
| `f_scale`  | optional [1] | scaling factor for `f` array data|
| `f_col`  | **required** (if not array) | column name in profile file with profile data|
| `f_index_col`| optional [0] | index column in profile file|
| `f_sheet_name`| **required** (if Excel) | sheet name in Excel book with profile data|
| `savename`| optional [`bessopt.xlsx] | Excel file to save the optimization results|
| `run_no_fix`| optional [False] | If True a scenario with solar equal to the minimum HC without battery is performed |
| 'solver' | optional [cbc] | Solver to pass to the pyomo model|

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