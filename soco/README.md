# Socio-Grid Co-simulation (SOCO) Example

This example uses GridLAB-D, HELICS, and a custom Python agent
to produce metrics for a community resilience hub, including
energy and environmental justice (EEJ) factors. It provides a
starting point for sprint studies that include EEJ factors.

[Summary](../docs/assets/soco_test.pdf)

## Steps to run simulations:

This example has been tested on Ubuntu, not Windows.

1. Need `pip3 install tesp_support`, and Helics
2. `python3 prepare_case.py` to make a weather file, and GridLAB-D metrics dictionary
3. `./testglm.sh` to run a time-series power flow, without events
4. `python3 plots.py` to summarize and plot metrics
5. `./run.sh` to run a HELICS federation that simulates a utility outage after 2 days
6. `python3 plots.py` again to summarize and plot metrics

The SOCO agent is in *soco.py*, configured in socoConfig.json:

1. Opens the utility switch after 2 days
2. During the event, controls battery discharging and charging
3. During the event, dispatches the diesel generator as a swing machine
4. At the event start, suppresses some of the non-critical load in homes
   (Because of the internal GridLAB-D schedule implementation, these messages
    have to be sent repeatedly. In TESP, schedules are implemented in the agents
    to avoid repeated messages, which are very inefficient. An alternative
    might be to shed load components by opening switches, which would have
    to be added to *soco\_test.glm*)

The Diesel Generator (DG) is 600 kW, 650 kVA, $0.5/kwh, 2.3 lbs CO2/kwh, 0.221 lbs PM/kwh

