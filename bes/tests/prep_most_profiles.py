# Copyright (C) 2021-2023 Battelle Memorial Institute
# file: wind_to_most.py
# converts output from 5 synthetic wind plants to a MOST profile function
# also prepares the responsive and fixed load profile functions

import numpy as np
import mpow_utilities as mpow
import sys
import os

import matplotlib.pyplot as plt

if __name__ == '__main__':
  plt.rcParams['savefig.directory'] = os.getcwd()
  hours = 72
  load_scale = 1.0
  resp_scale = 1.0 / 3.0
  if len(sys.argv) > 1:
    hours = int(sys.argv[1])
  wind_plants = np.array ([99.8, 1657.0, 2242.2, 3562.2, 8730.3])
  wind_plant_rows = [14, 15, 16, 17, 18]
  wind_plant_buses = [1, 3, 4, 6, 7]
  load_rows = [1, 2, 3, 4, 5, 6, 7, 8]

  # archived load data from TESP example of ERCOT8
  base_load = np.array ([[7182.65, 6831.0, 6728.83, 6781.1, 6985.44, 7291.94, 7650.72, 8104.54, 8522.71, 8874.36, 9173.74, 9446.98, 9736.85, 10078.99, 10466.28, 10855.94, 11179.08, 11319.26, 11200.46, 10893.96, 10630.22, 10326.1, 9781.99, 8810.21],
  [7726.69, 6840.09, 6637.09, 6603.94, 6719.95, 6972.67, 7295.82, 7693.55, 8140.99, 8518.01, 8837.02, 9114.6, 9383.9, 9686.33, 10046.77, 10436.22, 10800.8, 11053.52, 11078.38, 10862.95, 10560.51, 10311.93, 9930.77, 9255.46],
  [162.23, 150.74, 147.38, 147.58, 151.14, 157.34, 164.74, 174.24, 183.88, 191.86, 198.73, 204.8, 210.94, 218.0, 226.31, 234.89, 242.62, 247.1, 246.18, 240.24, 233.97, 228.03, 218.06, 200.84],
  [2097.83, 1715.67, 1634.79, 1612.55, 1625.69, 1676.24, 1750.04, 1836.99, 1946.17, 2045.25, 2129.17, 2200.95, 2265.65, 2335.41, 2418.31, 2511.32, 2604.34, 2680.16, 2712.51, 2681.17, 2608.38, 2544.69, 2470.88, 2337.43],
  [3922.54, 3492.58, 3390.92, 3376.09, 3437.51, 3568.83, 3731.92, 3937.36, 4163.99, 4356.73, 4519.81, 4661.72, 4801.51, 4956.12, 5140.39, 5337.36, 5523.74, 5650.82, 5663.53, 5549.16, 5396.66, 5267.47, 5070.49, 4723.14],
  [232.03, 198.01, 191.14, 189.66, 192.44, 199.23, 208.37, 219.33, 232.2, 243.34, 252.82, 260.91, 268.66, 277.18, 287.27, 298.32, 309.02, 316.94, 318.77, 313.37, 304.59, 297.45, 287.36, 269.27],
  [2650.16, 2535.62, 2503.87, 2529.95, 2610.47, 2727.27, 2864.48, 3034.58, 3187.67, 3315.82, 3425.81, 3527.87, 3636.74, 3766.01, 3911.17, 4055.18, 4170.85, 4212.81, 4159.51, 4043.84, 3947.45, 3827.25, 3612.92, 3213.76],
  [56.55, 51.95, 50.65, 50.57, 51.68, 53.72, 56.25, 59.4, 62.76, 65.57, 67.97, 70.06, 72.15, 74.53, 77.34, 80.29, 83.0, 84.73, 84.61, 82.72, 80.5, 78.53, 75.32, 69.74]])

  # read the LARIMA model profiles, col0=hour, col1..n=MW output
  np.set_printoptions(precision=3)
  dat = np.loadtxt ('wind_plants.dat', delimiter=',')
  nwindpoints = np.shape(dat)[0]
  if hours > nwindpoints:
    print ('ERROR: requested hours={:d} is more than available wind hours={:d}'.format(hours, nwindpoints))
    print ('Modify and run wind_plants.py to create enough synthetic wind data')
    quit()
  else:
    wind = dat[:hours,1:]
    print('wind data shape', np.shape(dat), 'using', np.shape(wind))

  # pad and plot the load profiles to cover requested number of hours
  fixed_load = base_load
  while np.shape(fixed_load)[1] < hours:
    fixed_load = np.hstack((fixed_load, base_load))
    print ('  stacking load shapes to', np.shape(fixed_load))
  fixed_load = fixed_load[:,:hours]
  print ('using fixed load shape', np.shape(fixed_load))
  responsive_load = resp_scale * fixed_load

  cset = ['red', 'blue', 'green', 'magenta', 'cyan', 'orange', 'lime', 'silver',
          'gold', 'pink', 'tan', 'peru', 'darkgray']

  fig, ax = plt.subplots(1, 2, figsize=(18,10), constrained_layout=True)
  fig.suptitle ('MOST Profiles for {:d} Hours, Load Scale = {:.3f}, Resp/Fixed = {:.3f}'.format (hours, load_scale, resp_scale))
  ax[0].set_title('Wind Plant Output')
  ax[1].set_title('Fixed Bus Loads')
  h = np.linspace (0, hours-1, hours)
  ld = np.transpose(fixed_load)
  for i in range(len(wind_plant_buses)):
    bus = wind_plant_buses[i]
    ax[0].plot (h, wind[:,i], label='Bus {:d}'.format(bus), color=cset[bus-1])
  for i in range(len(load_rows)):
    bus = load_rows[i]
    ax[1].plot (h, ld[:,i], label='Bus {:d}'.format(bus), color=cset[bus-1])
  for i in range(2):
    ax[i].grid (linestyle = '-')
    ax[i].set_xlim(0, hours)
    ax[i].set_xlabel ('Hour')
    ax[i].set_ylabel ('MW')
    ax[i].legend()
  plt.show()
  plt.close()

  # write the load profiles
  fp = open('test_damunresp.m', 'w')
  print('function unresp = test_damunresp', file=fp)
  mpow.write_most_table_indices(fp)
  print("""  unresp = struct( ...
    'type', 'mpcData', ...
    'table', CT_TBUS, ...
    'rows', {:s}, ...
    'col', PD, ...
    'chgtype', CT_REP, ...
    'values', [] );""".format(str(load_rows)), file=fp)
  print('  scale = {:.3f};'.format(load_scale), file=fp)
  for i in range(len(load_rows)):
    rownum = load_rows[i]
    vals = str([round(v, 2) for v in fixed_load[i,:hours]])
    mvals = vals.replace(',', ';')
    print("""  unresp.values(:, 1, {:d}) = scale * {:s};""".format(rownum, mvals), file=fp)
  print('end', file=fp)
  fp.close()

  fp = open('test_damresp.m', 'w')
  print('function resp = test_damresp', file=fp)
  mpow.write_most_table_indices(fp)
  print("""  resp = struct( ...
    'type', 'mpcData', ...
    'table', CT_TLOAD, ...
    'rows', {:s}, ...
    'col', CT_LOAD_DIS_P, ...
    'chgtype', CT_REP, ...
    'values', [] );""".format(str(load_rows)), file=fp)
  print('  scale = {:.3f};'.format(load_scale), file=fp)
  for i in range(len(load_rows)):
    rownum = load_rows[i]
    vals = str([round(v, 2) for v in responsive_load[i,:hours]])
    mvals = vals.replace(',', ';')
    print("""  resp.values(:, 1, {:d}) = scale * {:s};""".format(rownum, mvals), file=fp)
  print("""
    # per answer to https://github.com/MATPOWER/matpower/issues/106
    #   apply scaling to the total of responsive plus unresponsive load
    unresp = test_damunresp;
    resp.values = resp.values + unresp.values;""", file=fp)
  print('end', file=fp)
  fp.close()

  # write the wind plant profiles
  fp = open('test_damwind.m', 'w')
  print('function wind = test_damwind', file=fp)
  mpow.write_most_table_indices(fp)
  print("""  wind = struct( ...
    'type', 'mpcData', ...
    'table', CT_TGEN, ...
    'rows', {:s}, ...
    'col', PMAX, ...
    'chgtype', CT_REP, ...
    'values', [] );""".format(str(wind_plant_rows)), file=fp)
  for i in range(len(wind_plant_rows)):
    vals = str([round(v, 2) for v in wind[:hours,i]])
    mvals = vals.replace(',', ';')
    print("""  wind.values(:, 1, {:d}) = {:s};""".format(i+1, mvals), file=fp)
  print('end', file=fp)
  fp.close()



