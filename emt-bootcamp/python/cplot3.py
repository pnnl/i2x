# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: cplot2.py
""" Plots COMTRADE channels from switching and average model cases.
"""

import sys
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from comtrade import Comtrade

kVLNbase = 230.0 / math.sqrt(3.0)
MVAbase = 100.0
kAbase = MVAbase / kVLNbase / 3.0

def scale_factor(lbl):
  if 'P' in lbl:
    return 1.0 / MVAbase
  elif 'Q' in lbl:
    return 1.0 / MVAbase
  elif 'I' in lbl:
    return 1.0 / kAbase / math.sqrt(2.0)
  elif 'Vrms' in lbl:
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

def show_case_plot(channels, units, case_title):
  t = channels['t']
  fig, ax = plt.subplots(5, 1, sharex = 'col', figsize=(15,10), constrained_layout=True)
  fig.suptitle ('Case: ' + case_title)
  for lbl in ['VA', 'VB', 'VC']:
    ax[0].plot (t, scale_factor(lbl) * channels[lbl], label=lbl)
    ax[0].set_ylabel ('V(t) [pu]')
  for lbl in ['IA', 'IB', 'IC']:
    ax[1].plot (t, scale_factor(lbl) * channels[lbl], label=lbl)
    ax[1].set_ylabel ('I(t) [pu]')
  for lbl in ['Vrms']:
    ax[2].plot (t, scale_factor(lbl) * channels[lbl], label=lbl)
    ax[2].set_ylabel ('V [pu]')
  for lbl in ['P', 'Q']:
    ax[3].plot (t, scale_factor(lbl) * channels[lbl], label=lbl)
    ax[3].set_ylabel ('P, Q [pu]')
  for lbl in ['F']:
    ax[4].plot (t, scale_factor(lbl) * channels[lbl], label=lbl)
    ax[4].set_ylabel ('F [Hz]')
  for i in range(5):
    ax[i].grid()
    ax[i].legend()
#    ax[i].set_xlim (t[0], t[-1])
    ax[i].set_xlim (0.75, 1.75)
  ax[4].set_xlabel ('seconds')
  plt.show()
  plt.close()

def show_comparison_plot (dm, avm, units):
  fig, ax = plt.subplots(4, 1, sharex = 'col', figsize=(15,10), constrained_layout=True)
  fig.suptitle ('Comparing Average and Switching Models')

  channel_labels = ['Vrms', 'P', 'Q', 'F']
  y_labels = ['Vrms [pu]', 'P [pu]', 'Q [pu]', 'F [Hz]']
  x_ticks = [0.75, 1.00, 1.25, 1.50, 1.75]

  for i in range(4):
    lbl = channel_labels[i]
    ax[i].set_ylabel (y_labels[i])
    ax[i].plot (dm['t'], scale_factor(lbl) * dm[lbl], label='DM')
    ax[i].plot (avm['t'], scale_factor(lbl) * avm[lbl], label='AVM')
    ax[i].set_xticks (x_ticks)
    ax[i].set_xlim (x_ticks[0], x_ticks[-1])
    ax[i].grid()
    ax[i].legend()
  ax[3].set_xlabel ('Time [s]')
  plt.show()
  plt.close()

# load all the analog channels from each case into dictionaries of numpy arrays. Expecting:
#   1..3 = Va..Vc
#   4..6 = Ia..Ic
#   7 = Vrms
#   8 = P
#   9 = Q
#   10 = F
def load_channels(comtrade_path):
  print (comtrade_path)
  rec = Comtrade ()
  rec.load (comtrade_path + '.cfg', comtrade_path + '.dat')
  t = np.array(rec.time)

  channels = {}
  units = {}
  channels['t'] = t
  print ('Channels ({:d} points) read from {:s}.cfg:'.format (len(t), comtrade_path))
  for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i].strip()
    # for PSCAD naming convention, truncate the channel at first colon, if one exists
    idx = lbl.find(':')
    if idx >= 0:
      lbl = lbl[0:idx]
    ch_config = rec.cfg.analog_channels[i]
    scale = 1.0
    if ch_config.pors.upper() == 'P':
      scale = ch_config.secondary / ch_config.primary
    elif ch_config.pors.upper() == 'S':
      scale = ch_config.primary / ch_config.secondary
    print ('  "{:s}" [{:s}] scale={:.6e}'.format(lbl, ch_config.uu, scale))
    channels[lbl] = scale * np.array (rec.analog[i])
    units[lbl] = ch_config.uu

  return channels, units

def show_test_plot (channels, units, case_title):
  t = channels['t']
  labels = []
  for lbl in channels:
    if lbl != 't':
      labels.append(lbl)
  fig, ax = plt.subplots(len(labels), 1, sharex = 'col', figsize=(12,10), constrained_layout=True)
  fig.suptitle ('Case: ' + case_title)
  for i in range(len(labels)):
    lbl = labels[i]
    ax[i].plot(t, channels[lbl], label=lbl)
    ax[i].set_ylabel (units[lbl])
    ax[i].grid()
    ax[i].legend()
  ax[i].set_xlabel ('Time [s]')
  ax[i].set_xlim (t[0], int(t[-1]+0.5))
  plt.show()
  plt.close()

if __name__ == '__main__':
  bPSCAD = True
  if len(sys.argv) > 1:
    if int(sys.argv[1]) == 1:
      bPSCAD = False

  setup_plot_options()

  # set the session_path to match location of your unzipped sample cases
  if bPSCAD:
    session_path = 'c:/temp/i2x/pscad'
    dm_path = os.path.join (session_path, 'Solar3dm.if18_x86/rank_00001/Run_00001/DM')
    avm_path = os.path.join (session_path, 'Solar3avm.if18_x86/rank_00001/Run_00001/AVM')
  else:
    session_path = 'c:/temp/i2x/emtp'
    dm_path = os.path.join (session_path, 'dm')
    avm_path = os.path.join (session_path, 'avm')

  dm_channels, dm_units = load_channels (dm_path)
  avm_channels, avm_units = load_channels (avm_path)

  show_case_plot (dm_channels, dm_units, 'Switching Model')
  show_case_plot (avm_channels, avm_units, 'Average Model')
  show_comparison_plot (dm=dm_channels, avm=avm_channels, units=dm_units)

  #  show_test_plot (dm_channels, dm_units, dm_path)
  #  show_test_plot (avm_channels, avm_units, avm_path)

