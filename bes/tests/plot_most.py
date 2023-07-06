# Copyright (C) 2020-2023 Battelle Memorial Institute
# file: plot_most.py
# reads and plots a MOST solution, saved from most_summary MATPOWER command

import numpy as np
import matplotlib.pyplot as plt
import math
import os
import sys
import mpow_utilities as mpow

def bus_color(key):
  if key == '1':
    return 'b'
  if key == '2':
    return 'g'
  if key == '3':
    return 'r'
  if key == '4':
    return 'c'
  if key == '5':
    return 'm'
  if key == '6':
    return 'y'
  if key == '7':
    return 'k'
  if key == '8':
    return 'cadetblue'
  return 'k'

def unit_width(d, key):
  if d['generators'][key]['bustype'] == 'swing':
    return 2.0
  return 1.0

if __name__ == '__main__':
  plot_branch_prices = False
  fname = 'msout.txt'
  if len(sys.argv) > 1:
    fname = sys.argv[1]
    if len(sys.argv) > 2:
      if int(sys.argv[2]) > 0:
        plot_branch_prices = True
  use_wind = True

  plt.rcParams['savefig.directory'] = os.getcwd()

  d = mpow.read_matpower_casefile ('test_case.m')
  mpow.summarize_casefile (d, 'Input Data')

  f, nb, ng, nl, ns, nt, nj_max, nc_max, psi, Pg, Pd, Rup, Rdn, SoC, Pf, u, lamP, muF = mpow.read_most_solution(fname)
  print ('f={:.4e}, nb={:d}, ng={:d}, nl={:d}, ns={:d}, nt={:d}, nj_max={:d}, nc_max={:d}'.format(f, nb, ng, nl, ns, nt, nj_max, nc_max))
  print ('Pg', np.shape(Pg))
  print ('Pd', np.shape(Pd))
  print ('Pf', np.shape(Pf))
  print ('u', np.shape(u))
  print ('lamP', np.shape(lamP))
  print ('muF', np.shape(muF))

  np.set_printoptions(precision=3)
  h = np.linspace (1.0, 24.0, num=nt) - 0.5
  #print (lamP)

  # build list of generation by fuel type
  fuel_Pg = {}
  for fuel in ['ng', 'wind', 'solar', 'coal', 'nuclear', 'dl']:
    fuel_Pg[fuel] = np.zeros(nt)
  for i in range(ng):
    fuel = d['genfuel'][i]
    gen = Pg[i]
    fuel_Pg[fuel] += gen

  if use_wind:
    resp_start = 18
  else:
    resp_start = 13
  Presp = np.abs(fuel_Pg['dl'])
  Pfixed = np.sum(Pd, axis=0)
  AvgSteam = np.mean(fuel_Pg['coal'] + fuel_Pg['nuclear'])
  AvgGas = np.mean(fuel_Pg['ng'])
  AvgSolar = np.mean(fuel_Pg['solar'])
  AvgWind = np.mean(fuel_Pg['wind'])
  AvgFixed = np.mean(Pfixed)
  AvgResp = np.mean(Presp)
  AvgErr = AvgSteam + AvgGas + AvgWind - AvgFixed - AvgResp
  print ('Average Psteam={:.2f}, Pgas={:.2f}, Pwind={:.2f}, Psolar={:.2f}, Pfixed={:.2f}, Presp={:.2f}, Perr={:.2f}'.format (AvgSteam, 
        AvgGas, AvgWind, AvgSolar, AvgFixed, AvgResp, AvgErr))
  #quit()

  cset = ['red', 'blue', 'green', 'magenta', 'cyan', 'orange', 'lime', 'silver',
          'gold', 'pink', 'tan', 'peru', 'darkgray']
  fig, ax = plt.subplots(2, 4, sharex = 'col', figsize=(18,10), constrained_layout=True)
  fig.suptitle ('MOST Solution from {:s}'.format(fname))
  tmin = 0.0
  tmax = 24.0
  xticks = [0,6,12,18,24]
  for i in range(2):
    for j in range(4):
      ax[i,j].grid (linestyle = '-')
      ax[i,j].set_xlim(tmin,tmax)
      ax[i,j].set_xticks(xticks)

  ax[0,0].set_title ('Unit Commitment Status')
  usched = np.zeros (len(h))
  if resp_start >= 14:
    ax[0,0].set_ylim (0, 20)
    ax[0,0].set_yticks (np.linspace(0, 20, 11))
  else:
    ax[0,0].set_ylim (0, 14)
    ax[0,0].set_yticks (np.linspace(0, 14, 8))
  ax[0,0].set_ylabel ('Unit #')
  off_val = -1.0
  for i in range(resp_start):
    on_val = i + 1.0
    for j in range(len(h)):
      if u[i,j] < 0.001:
        usched[j] = off_val
      else:
        usched[j] = on_val
    clr, lbl = mpow.unit_color_label (genfuel = str(d['genfuel'][i]))
    ax[0,0].plot(h, usched, marker='+', linestyle='None', color=clr)

  ax[0,1].set_title ('Bus Locational Marginal Price (LMP)')
  for i in range(nb):
    ax[0,1].plot(h, lamP[i,:], label='Bus{:d}'.format (i+1), color = cset[i])
  ax[0,1].set_ylabel ('$/MWhr')
  ax[0,1].legend()

  if plot_branch_prices:
    ax[0,2].set_title ('Branch Shadow Prices (muF)')
    for i in range(nl):
      ax[0,2].plot(h, muF[i,:], label='Ln{:d}'.format (i+1), color = cset[i])
    ax[0,2].set_ylabel ('$/MWhr')
    ax[0,2].legend()
  else:
    ax[0,2].set_title ('Branch Flows')
    for i in range(nl):
      ax[0,2].plot(h, 0.001 * np.abs(Pf[i,:]), label='Ln{:d}'.format (i+1), color = cset[i])
    ax[0,2].set_ylabel ('GW')

  ax[1,0].set_title ('Unit Dispatch (in Bus Colors)')
  for i in range(resp_start):
    bus_idx = int(float(d['gen'][i][mpow.GEN_BUS])) - 1
    ax[1,0].plot(h, 0.001 * Pg[i,:], label='Gen{:d}'.format (i+1), color = cset[bus_idx])
  ax[1,0].set_ylabel ('GW')

  ax[1,1].set_title ('Fixed Bus Loads')
  for i in range(nb):
    ax[1,1].plot(h, 0.001 * Pd[i,:], label='Bus{:d}'.format (i+1), color = cset[i])
  ax[1,1].set_ylabel ('GW')
  ax[1,1].legend()

  ax[1,2].set_title ('Responsive Bus Loads')
  for i in range(nb):
    ax[1,2].plot(h, 0.001 * np.abs(Pg[i+resp_start,:]), label='Bus{:d}'.format (i+1), color = cset[i])
  ax[1,2].set_ylabel ('GW')
  ax[1,2].legend()

  ax[0,3].set_title ('System Generation')
  for fuel in ['solar', 'wind', 'ng', 'coal', 'nuclear']:
    clr, lbl = mpow.unit_color_label (fuel)
    ax[0,3].plot(h, 0.001 * fuel_Pg[fuel], label=lbl, color=clr)
  ax[0,3].plot(h, 0.001 * (Pfixed + Presp), label='Load', color='magenta')
  ax[0,3].set_ylabel ('GW')
  ax[0,3].legend()

  ax[1,3].set_title ('System Load Components')
  ax[1,3].plot(h, 0.001 * (Pfixed + Presp), label='Total', color='magenta')
  ax[1,3].plot(h, 0.001 * Pfixed, label='Fixed', color='red')
  ax[1,3].plot(h, 0.001 * Presp, label='Responsive', color='blue')
  ax[1,3].set_ylabel ('GW')
  ax[1,3].legend()

  for j in range(4):
    ax[1,j].set_xlabel ('Hour')
  plt.show()
