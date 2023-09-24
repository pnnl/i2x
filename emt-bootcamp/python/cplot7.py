# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: cplot7.py
""" Plots COMTRADE channels from system study cases.
"""

import sys
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from comtrade import Comtrade

plt.rcParams['savefig.directory'] = os.getcwd()

kVLNbase = 345.0 / math.sqrt(3.0)
MVAbase = 300.0
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
  plt.rc('legend', fontsize=10)

def show_case_plot(channels, units, title, bPSCAD, tmax=40.0, PNGName=None):
  x_ticks = np.linspace (0.0, tmax, 11)
  t = channels['t']
  fig, ax = plt.subplots(3, 1, sharex = 'col', figsize=(15,10), constrained_layout=True)
  fig.suptitle (title)
  tags = ['Vrms', 'P', 'Q']
  labels = ['Vrms [pu]', 'P [pu]', 'Q [pu]']
  for i in range(3):
    ax[i].plot (t, scale_factor(tags[i], bPSCAD) * channels[tags[i]], label=labels[i])
    ax[i].set_xticks (x_ticks)
    ax[i].set_xlim (x_ticks[0], x_ticks[-1])
    ax[i].grid()
    ax[i].legend(loc='lower right')
  ax[2].set_xlabel ('seconds')
  if PNGName is not None:
    plt.savefig(PNGName)
  plt.show()
  plt.close(fig)

def show_comparison_plot(chd, unitd, title, bPSCAD, tmax=40.0, PNGName=None):
  fig, ax = plt.subplots(3, 1, sharex = 'col', figsize=(15,10), constrained_layout=True)
  fig.suptitle (title)

  x_ticks = np.linspace (0.0, tmax, 11)
  channel_labels = ['Vrms', 'P', 'Q']
  y_labels = ['Vrms [pu]', 'P [pu]', 'Q [pu]']

  for key in chd:
    ch = chd[key]
    for i in range(3):
      lbl = channel_labels[i]
      ax[i].plot (ch['t'], scale_factor(lbl, bPSCAD) * ch[lbl], label=key)

  for i in range(3):
    ax[i].set_ylabel (y_labels[i])
    ax[i].set_xticks (x_ticks)
    ax[i].set_xlim (x_ticks[0], x_ticks[-1])
    ax[i].grid()
    ax[i].legend(loc='lower right')
  ax[2].set_xlabel ('Time [s]')

  if PNGName is not None:
    plt.savefig(PNGName)
  plt.show()
  plt.close(fig)

# load all the analog channels from each case into dictionaries of numpy arrays. Expecting:
#   Vrms, P, Q
def load_channels(comtrade_path, bDebug=False):
  if bDebug:
    print (comtrade_path)
  rec = Comtrade ()
  rec.load (comtrade_path + '.cfg', comtrade_path + '.dat')
  t = np.array(rec.time)

  channels = {}
  units = {}
  channels['t'] = t
  print ('{:d} channels ({:d} points) read from {:s}.cfg'.format (rec.analog_count, len(t), comtrade_path))
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
    if bDebug:
      print ('  "{:s}" [{:s}] scale={:.6e}'.format(lbl, ch_config.uu, scale))
    channels[lbl] = scale * np.array (rec.analog[i])
    units[lbl] = ch_config.uu

  return channels, units

if __name__ == '__main__':
  bPSCAD = True
  bSavePNG = False
  if len(sys.argv) > 1:
    if int(sys.argv[1]) == 1:
      bPSCAD = False
    if len(sys.argv) > 2:
      if int(sys.argv[2]) == 1:
        bSavePNG = True

  setup_plot_options()

  cases = ['L13_x0', 'L13_xL15', 'L13_xL4',
           'L15_x0', 'L15_xL13', 'L15_xL4',
           'L4_x0', 'L4_xL13', 'L4_xL15']
  #cases = ['L13_x0']

  # set the session_path to match location of your unzipped sample cases
  if bPSCAD:
    session_path = 'c:/temp/i2x/pscad/SolarSystem.if18_x86/rank_00001/Run_00001'
    plant = 'Solar'
    tmax = 6.0
  else:
    session_path = 'c:/temp/i2x/emtp'
    plant = 'Wind'
    tmax = 10.0
  if bSavePNG:
    PNGName = '{:s}_study.png'.format (plant)
  else:
    PNGName = None

  channels = {}
  units = {}
  for tag in cases:
    tag_path = os.path.join (session_path, tag)
    channels[tag], units[tag] = load_channels (tag_path)
    #show_case_plot (channels[tag], units[tag], 'System Study Case: {:s} {:s}'.format(plant, tag), bPSCAD, tmax, PNGName)

  title = '300-MW {:s} Plant Study at Bus 14 of IEEE 39-bus Test System'.format (plant)
  show_comparison_plot (channels, units, title, bPSCAD, tmax, PNGName)

