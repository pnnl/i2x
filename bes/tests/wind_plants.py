# Copyright (C) 2021-2023 Battelle Memorial Institute
# file: wind_plants.py
# plots output from 5 synthetic wind plants in the ERCOT 8-bus test system
# see https://doi.org/10.1016/j.apenergy.2020.115182 for description of the 8-bus test system
# see https://doi.org/10.1109/TPWRS.2009.2033277 for details on the synthetic wind plant method

import numpy as np
import matplotlib.pyplot as plt
import math
import os
import sys

if __name__ == '__main__':
  plt.rcParams['savefig.directory'] = os.getcwd()
  seed = None
  if len(sys.argv) > 1:
    seed = int(sys.argv[1])
    np.random.seed(seed)

  dt = 3600 # seconds, use hourly for MOST
  days = 3
  tticks = np.linspace(0, days*24, days*4+1)

  Pnorm = 165.6

  # create normalized LARIMA models for the wind plants
  wind_plants = np.array ([99.8, 1657.0, 2242.2, 3562.2, 8730.3])

  nplants = wind_plants.shape[0]
  n = 24 * days + 1

  h = np.linspace (0, n - 1, n)
  p = np.zeros (shape = (nplants, n))
  alag = np.zeros (nplants)
  ylag = np.zeros (nplants)
  Theta0 = np.ones (nplants)
  Theta1 = np.ones (nplants)
  StdDev = np.ones (nplants)
  Psi1 = np.ones (nplants)
  Ylim = np.ones (nplants)

  print ('Simulating', days, 'days with seed', seed)
  print (' #      MW   scale  Theta0  Theta1  StdDev    Psi1    Ylim')
  for j in range (nplants):
    scale = wind_plants [j] / Pnorm
    Theta0[j] = 0.05 * math.sqrt (scale)
    Theta1[j] = -0.1 * (scale)
    StdDev[j] = math.sqrt (1.172 * math.sqrt (scale))
    Psi1[j] = 1.0
    Ylim[j] = math.sqrt (wind_plants[j])
    alag[j] = Theta0[j]
    ylag[j] = Ylim[j]
    print ('{:2d} {:7.2f} {:7.4f} {:7.4f} {:7.4f} {:7.4f} {:7.4f} {:7.2f}'.format(j+1, wind_plants[j], scale, Theta0[j], Theta1[j], StdDev[j], Psi1[j], Ylim[j]))

  # time-stepping to generate the hourly plant outputs
  i = 0
  ts = 0
  tmax = days * 24 * 3600
  tnext_wind = 0
  wind_period = 3600

  while ts <= tmax:
    if ts >= tnext_wind:
      for j in range (nplants):
        if i > 0:
          a = np.random.normal (0.0, StdDev[j])
          y = Theta0[j] + a - Theta1[j] * alag[j] + Psi1[j] * ylag[j]
          alag[j] = a
        else:
          y = ylag[j]
        if y > Ylim[j]:
          y = Ylim[j]
        elif y < 0.0:
          y = 0.0
        p[j,i] = y * y
        if i > 0:
          ylag[j] = y
      i += 1
      tnext_wind += wind_period
    ts += dt

  # save hourly outputs for MOST
  np.savetxt ('wind_plants.dat', np.transpose(np.vstack((h, p))), fmt='%.4f', delimiter=',')

  # summarize each plant
  CF = np.zeros (nplants)
  COV = np.zeros (nplants)
  msg = [None] * nplants
  print (' #      MW      CF     COV')
  sys_capacity = 0.0
  sys_average = 0.0
  sys_variance = 0.0
  for j in range (nplants):
    p_avg = p[j,:].mean()
    p_std = p[j,:].std()
    CF[j] = p_avg / wind_plants[j]
    COV[j] = p_std / p_avg
    sys_capacity += wind_plants[j]
    sys_average += p_avg
    sys_variance += (p_std*p_std)
    msg[j] = '{:.1f}'.format (wind_plants[j]) + ' MW, CF = ' + '{:.2f}'.format (CF[j]) + ', COV = ' + '{:.2f}'.format (COV[j])  
    print ('{:2d} {:7.2f} {:7.4f} {:7.4f}'.format(j+1, wind_plants[j], CF[j], COV[j]))
  sys_CF = sys_average/sys_capacity
  sys_COV = math.sqrt(sys_variance)/sys_average
  print ('System capacity={:.2f} MW, CF={:.4f}, COV={:.4f}'.format (sys_capacity, sys_CF, sys_COV))

  # plot each plant
  fig, ax = plt.subplots(nplants, 1, sharex = 'col', figsize=(16,10), constrained_layout=True)
  fig.suptitle ('LARIMA Output for {:d} Wind Plants in ERCOT 8-Bus Model, MW={:.2f}, CF={:.4f}, COV={:.4f}, Seed={:s}'.format(nplants, sys_capacity, sys_CF, sys_COV, str(seed)))

  for j in range (nplants):
    ax[j].set_title (msg[j])
    ax[j].set_ylabel ('Plant {:d} MW'.format(j+1))
    ax[j].plot (h, p[j,:], 'r')
    ax[j].set_xticks(tticks)
    ax[j].set_xlim (tticks[0], tticks[-1])
    ax[j].set_ylim (0.0)
    ax[j].grid()
  ax[nplants-1].set_xlabel ('Hours')

  plt.show()



