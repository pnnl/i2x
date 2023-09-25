# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: cplot5.py
""" Plots COMTRADE channels from plant model test cases.
"""

import sys
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from comtrade import Comtrade

plt.rcParams['savefig.directory'] = os.getcwd()

kVLNbase = 230.0 / math.sqrt(3.0)
MVAbase = 100.0
kAbase = MVAbase / kVLNbase / 3.0

flats = ['fsicrv', 'fsicrq0', 'fsicrqp', 'fsicrqn', 'fsicrpf0', 'fsicrpfp', 'fsicrpfn',
         'fsminv', 'fsminq0', 'fsminqp', 'fsminqn', 'fsminpf0', 'fsminpfp', 'fsminpfn']

uvrts = ['uvq03sag', 'uvq03pg', 'uvq01pg', 'uvq02pg', 'uvq02p', 
         'uvqp3sag', 'uvqp3pg', 'uvqp1pg', 'uvqp2pg', 'uvqp2p', 
         'uvqn3sag', 'uvqn3pg', 'uvqn1pg', 'uvqn2pg', 'uvqn2p']

ovrts = ['ovq0', 'ovqp', 'ovqn']

freqs = ['oficr', 'uficr', 'ofmin', 'ufmin']

angles = ['anicr', 'apicr', 'anmin', 'apmin']

steps = ['stvref', 'stqref', 'stpfref', 'stpref']

test_suites = {'fs': {'title': 'Weak-grid model initialization tests', 'files': flats, 
                      'tmax_pscad': 20.0, 'tmax_emtp':20.0},
               'uv': {'title': 'Weak-grid undervoltage ride-through tests', 'files': uvrts, 
                      'tmax_pscad': 20.0, 'tmax_emtp':20.0},
               'ov': {'title': 'Weak-grid overvoltage ride-through tests', 'files': ovrts, 
                      'tmax_pscad': 20.0, 'tmax_emtp':20.0},
               'fr': {'title': 'Weak-grid frequency ride-through tests', 'files': freqs, 
                      'tmax_pscad': 40.0, 'tmax_emtp':40.0},
               'an': {'title': 'Weak-grid angle ride-through tests', 'files': angles, 
                      'tmax_pscad': 40.0, 'tmax_emtp':30.0},
               'st': {'title': 'Control reference step tests', 'files': steps, 
                      'tmax_pscad': 50.0, 'tmax_emtp':50.0}}

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
#  clr = plt.get_cmap('tab20c').colors
#  plt.axes().set_prop_cycle('color', clr)

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
  ax[4].set_xlabel ('seconds')
  plt.show()
  plt.close()

def show_comparison_plot (chd, unitd, title, bPSCAD, tmax, PNGName=None):
  fig, ax = plt.subplots(4, 1, sharex = 'col', figsize=(15,10), constrained_layout=True)
  fig.suptitle (title)

  channel_labels = ['Vrms', 'P', 'Q', 'F']
  y_labels = ['Vrms [pu]', 'P [pu]', 'Q [pu]', 'F [Hz]']
  x_ticks = np.linspace (0.0, tmax, 11)

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
    ax[i].legend(loc='lower right')
  ax[3].set_xlabel ('Time [s]')
#  if not bPSCAD:
#    ax[0].set_ylim (0.85, 1.1)

  if PNGName is not None:
    plt.savefig(PNGName)
  plt.show()
  plt.close(fig)

# load all the analog channels from each case into dictionaries of numpy arrays. Expecting:
#   1..3 = Va..Vc
#   4..6 = Ia..Ic
#   7 = Vrms
#   8 = P
#   9 = Q
#   10 = F
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

def process_test_suite (session_path, case_tag, bPSCAD, test_title, test_files, test_tmax, PNGName):
  channels = {}
  units = {}
  for tag in test_files:
    tag_path = os.path.join (session_path, '{:s}'.format (tag))
    channels[tag], units[tag] = load_channels (tag_path)
    if bPSCAD: # cosmetic initialization of the frequency plot
      channels[tag]['F'][0] = 60.0
    #show_case_plot (channels[tag], units[tag], 'Case {:s}'.format(tag), bPSCAD)
  title = '{:s}: {:s}'.format(test_title, case_tag)
  show_comparison_plot (channels, units, title, bPSCAD, test_tmax, PNGName)

if __name__ == '__main__':
  bPSCAD = True
  bSavePNG = False
  test = 'fs'
  test = 'uv'
  test = 'ov'
  test = 'fr'
  test = 'an'
  test = 'st'
  if len(sys.argv) > 1:
    if int(sys.argv[1]) == 1:
      bPSCAD = False
    if len(sys.argv) > 2:
      test = sys.argv[2]
      if len(sys.argv) > 3:
        if int(sys.argv[3]) == 1:
          bSavePNG = True

  setup_plot_options()

  # set the session_path to match location of your unzipped sample cases
  if bPSCAD:
    case_tag = 'Solar'
    session_path = 'c:/temp/i2x/pscad/Solar5.if18_x86/rank_00001/Run_00001'
    tmax = test_suites[test]['tmax_pscad']
  else:
    session_path = 'c:/temp/i2x/emtp'
    case_tag = 'Wind'
    tmax = test_suites[test]['tmax_emtp']
  if bSavePNG:
    PNGName = '{:s}_{:s}.png'.format (case_tag, test)
  else:
    PNGName = None

  process_test_suite (session_path, case_tag, bPSCAD, test_suites[test]['title'], 
                      test_suites[test]['files'], tmax, PNGName)

