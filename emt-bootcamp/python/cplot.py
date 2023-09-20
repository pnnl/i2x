# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: cplot.py
""" Plots 3 voltage and 3 current channels for the EMT bootcamp.
"""

import sys
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from comtrade import Comtrade

kVLNbase = 138.0 / math.sqrt(3.0)
MVAbase = 100.0
kAbase = MVAbase / kVLNbase / 3.0

# change sign of P and Q so power out of the plant is positive
def scale_factor(lbl):
  if 'P' in lbl:
    return -1.0 / MVAbase
  elif 'Q' in lbl:
    return -1.0 / MVAbase
  elif 'I' in lbl:
    return 1.0 / kAbase / math.sqrt(2.0)
  elif 'rms' in lbl:
    return 1.0
  elif 'V' in lbl:
    return 1.0 / kVLNbase / math.sqrt(2.0)
  return 1.0

def setup_plot_options():
  plt.rcParams['savefig.directory'] = os.getcwd()
  lsize = 12
  plt.rc('font', family='serif')
  plt.rc('xtick', labelsize=lsize)
  plt.rc('ytick', labelsize=lsize)
  plt.rc('axes', labelsize=lsize)
  plt.rc('legend', fontsize=lsize)

def show_group_plot(channels, root):
  # display the channels in groups of three
  labels = [lbl for lbl in channels]
  fig, ax = plt.subplots(3, 1, sharex = 'col', figsize=(12,10), constrained_layout=True)
  fig.suptitle ('Case: ' + root)
  for i in range(3):
    for j in range(3):
      lbl = labels[3*i + j]
      ax[i].plot(t, scale_factor(lbl) * channels[lbl], label=lbl)
    ax[i].grid()
    ax[i].legend()
  plt.show()
  plt.close()

def show_poc_plot(channels):
  fig, ax = plt.subplots(1, 1, sharex = 'col', figsize=(8,10), constrained_layout=True)
  for lbl in ['A7: Vrms', 'A8: P', 'A9: Q']:
    ax.plot (t, scale_factor(lbl) * channels[lbl], label=lbl)
  ax.set_xlim (0, 6)
  ax.set_ylabel ('perunit')
  ax.set_xlabel ('seconds')
  ax.legend()
  ax.grid()
  plt.show()
  plt.close()

def show_zoomed_q_plot(channels):
  fig, ax = plt.subplots(1, 1, sharex = 'col', figsize=(8,10), constrained_layout=True)
  for lbl in ['A9: Q']:
    ax.plot (t, scale_factor(lbl) * channels[lbl], label=lbl, color='green')
  ax.set_xlim (0.8, 2.0)
  ax.set_ylabel ('perunit')
  ax.set_xlabel ('seconds')
  ax.legend()
  ax.grid()
  plt.show()
  plt.close()

if __name__ == '__main__':
  setup_plot_options()
  root = '../PSCAD/COMTRADEtest/playback'
#  root = '../PSCAD/gen.if18_x86/rank_00001/Run_00001/playback'
  if len(sys.argv) > 1:
    root = sys.argv[1]

  # load all the analog channels into a dictionary of numpy arrays
  # 1..3 = Va..Vc
  # 4..6 = Ia..Ic
  # 7 = Vrms
  # 8 = P
  # 9 = Q
  rec = Comtrade ()
  rec.load (root + '.cfg', root + '.dat')
  t = np.array(rec.time)
  channels = {}
  print ('Channels ({:d} points) read from {:s}.cfg:'.format (len(t), root))
  for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i].strip()
    print ('  "{:s}"'.format(lbl))
    channels[lbl] = np.array (rec.analog[i])

  show_group_plot(channels, root)
  show_poc_plot(channels)
  show_zoomed_q_plot(channels)

