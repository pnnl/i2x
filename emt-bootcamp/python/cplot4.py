# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: cplot2.py
""" Plots COMTRADE channels from parametric fault cases.
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

def scale_factor(lbl, bPSCAD):
  if 'P' in lbl:
    return 1.0 / MVAbase
  elif 'Q' in lbl:
    return 1.0 / MVAbase
  elif 'I' in lbl:
    return 1.0 / kAbase / math.sqrt(2.0)
  elif 'Vrms' in lbl:
    if not bPSCAD:
      return 1.0 / kVLNbase
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
  plt.rc('legend', fontsize=6)

def show_case_plot(channels, units, case_title, bPSCAD):
  t = channels['t']
  fig, ax = plt.subplots(5, 1, sharex = 'col', figsize=(15,10), constrained_layout=True)
  fig.suptitle ('Case: ' + case_title)
  for lbl in ['VA', 'VB', 'VC']:
    ax[0].plot (t, scale_factor(lbl, bPSCAD) * channels[lbl], label=lbl)
    ax[0].set_ylabel ('V(t) [pu]')
  for lbl in ['IA', 'IB', 'IC']:
    ax[1].plot (t, scale_factor(lbl, bPSCAD) * channels[lbl], label=lbl)
    ax[1].set_ylabel ('I(t) [pu]')
  for lbl in ['Vrms']:
    ax[2].plot (t, scale_factor(lbl, bPSCAD) * channels[lbl], label=lbl)
    ax[2].set_ylabel ('V [pu]')
  for lbl in ['P', 'Q']:
    ax[3].plot (t, scale_factor(lbl, bPSCAD) * channels[lbl], label=lbl)
    ax[3].set_ylabel ('P, Q [pu]')
  for lbl in ['F']:
    ax[4].plot (t, scale_factor(lbl, bPSCAD) * channels[lbl], label=lbl)
    ax[4].set_ylabel ('F [Hz]')
  for i in range(5):
    ax[i].grid()
    ax[i].legend()
#    ax[i].set_xlim (t[0], t[-1])
    ax[i].set_xlim (0.75, 1.75)
  ax[4].set_xlabel ('seconds')
  plt.show()
  plt.close()

def show_fault_comparison_plot (chd, unitd, case_tag, bPSCAD):
  fig, ax = plt.subplots(4, 1, sharex = 'col', figsize=(15,10), constrained_layout=True)
  fig.suptitle ('Comparing Fault Cases: {:s}'.format(case_tag))

  channel_labels = ['Vrms', 'P', 'Q', 'F']
  y_labels = ['Vrms [pu]', 'P [pu]', 'Q [pu]', 'F [Hz]']
  x_ticks = [0.75, 1.00, 1.25, 1.50, 1.75]

  for key in chd:
    ch = chd[key]
    for i in range(4):
      lbl = channel_labels[i]
      ax[i].plot (ch['t'], scale_factor(lbl, bPSCAD) * ch[lbl], label=key)

  for i in range(4):
    ax[i].set_ylabel (y_labels[i])
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

if __name__ == '__main__':
  bPSCAD = True
  if len(sys.argv) > 1:
    if int(sys.argv[1]) == 1:
      bPSCAD = False

  setup_plot_options()

  cases = ['abcg80', 'abcg50', 'abcg25', 'abcg01',
           'ag80',   'ag50',   'ag25',   'ag01',
           'bc80',   'bc50',   'bc25',   'bc01']

  # set the session_path to match location of your unzipped sample cases
  if bPSCAD:
    case_tag = 'Solar'
    session_path = 'c:/temp/i2x/pscad/Solar4.if18_x86/rank_00001/Run_00001'
  else:
    session_path = 'c:/temp/i2x/emtp'
    case_tag = 'Wind'

  flt_channels = {}
  flt_units = {}
  for tag in cases:
    flt_path = os.path.join (session_path, '{:s}'.format (tag))
    flt_channels[tag], flt_units[tag] = load_channels (flt_path)
    show_case_plot (flt_channels[tag], flt_units[tag], 'Case {:s}'.format(tag), bPSCAD)
  show_fault_comparison_plot (flt_channels, flt_units, case_tag, bPSCAD)

