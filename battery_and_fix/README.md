# Battery Usage with Flexible Interconnection
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

## Running the Model
The model is built using [pyomo](https://www.pyomo.org/).
To run it the following installation steps are necessary:
## Install pyomo 
```
conda install -c conda-forge pyomo
```
Check version using:
```
>pyomo --version
Pyomo 6.7.2 (CPython 3.10.12 on Windows 10)
```
(output may be different)
## Install ipopt
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