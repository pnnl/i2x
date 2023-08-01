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

def scale_factor(lbl):
  if 'P' in lbl:
    return 1.0 / MVAbase
  elif 'Q' in lbl:
    return 1.0 / MVAbase
  elif 'I' in lbl:
    return 1.0 / kAbase / math.sqrt(2.0)
  elif 'rms' in lbl:
    return 1.0
  elif 'V' in lbl:
    return 1.0 / kVLNbase / math.sqrt(2.0)
  return 1.0

if __name__ == '__main__':
  plt.rcParams['savefig.directory'] = os.getcwd()
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
  for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    channels[lbl] = np.array (rec.analog[i])

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

