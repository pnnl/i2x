# Copyright (C) 2021-2023 Battelle Memorial Institute
# file: wind_to_most.py
# converts output from 5 synthetic wind plants to a MOST profile function
# also prepares the responsive and fixed load profile functions
# usage 'python prep_most_profiles.py [start=0] [hours=24]'

import numpy as np
import i2x.mpow_utilities as mpow
import sys
import os

import matplotlib.pyplot as plt

if __name__ == '__main__':
  plt.rcParams['savefig.directory'] = os.getcwd()
  start = 0
  hours = 24
  load_scale = 1.0
  resp_scale = 1.0 / 3.0
  if len(sys.argv) > 1:
    start = int(sys.argv[1])
    if len(sys.argv) > 2:
      hours = int(sys.argv[2])
  end = start + hours

  # read the hourly wind plant output into rows
  wind = mpow.ercot_wind_profile ('wind_plants.dat', start, end)
  if len(wind) == 0:
    print ('failed to read wind data')
    quit()

  # pad and plot the load profiles to cover requested number of hours
  fixed_load, responsive_load = mpow.ercot_daily_loads (start, end, resp_scale)

  cset = ['red', 'blue', 'green', 'magenta', 'cyan', 'orange', 'lime', 'silver',
          'gold', 'pink', 'tan', 'peru', 'darkgray']

  fig, ax = plt.subplots(1, 2, figsize=(18,10), constrained_layout=True)
  fig.suptitle ('MOST Profiles for {:d} Hours from {:d}-{:d}, Load Scale = {:.3f}, Resp/Fixed = {:.3f}'.format (hours, start, end, load_scale, resp_scale))
  ax[0].set_title('Wind Plant Output')
  ax[1].set_title('Fixed Bus Loads')
  h = np.linspace (0, hours-1, hours)
  ld = np.transpose(fixed_load)
  for i in range(len(mpow.ercot8_wind_plant_buses)):
    bus = mpow.ercot8_wind_plant_buses[i]
    ax[0].plot (h, wind[i,:], label='Bus {:d}'.format(bus), color=cset[bus-1])
  for i in range(len(mpow.ercot8_load_rows)):
    bus = mpow.ercot8_load_rows[i]
    ax[1].plot (h, ld[:,i], label='Bus {:d}'.format(bus), color=cset[bus-1])
  for i in range(2):
    ax[i].grid (linestyle = '-')
    ax[i].set_xlim(0, hours)
    ax[i].set_xlabel ('Hour')
    ax[i].set_ylabel ('MW')
    ax[i].legend()
  plt.show()
  plt.close()

  # write the load and wind profiles
  mpow.write_unresponsive_load_profile ('test_unresp', mpow.ercot8_load_rows, fixed_load[:,:hours], load_scale)
  mpow.write_responsive_load_profile ('test_resp', mpow.ercot8_load_rows, responsive_load[:,:hours], load_scale, 'test_unresp')
  mpow.write_wind_profile ('test_wind', mpow.ercot8_wind_plant_rows, wind[:,:hours])

