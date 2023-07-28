# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: cplot.py
""" Plots 3 voltage and 3 current channels for the EMT bootcamp.
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from comtrade import Comtrade

if __name__ == '__main__':
  plt.rcParams['savefig.directory'] = os.getcwd()
  root = '../PSCAD/COMTRADEtest/playback'
  if len(sys.argv) > 1:
    root = sys.argv[1]

  # load all the analog channels into a dictionary of numpy arrays
  rec = Comtrade ()
  rec.load (root + '.cfg', root + '.dat')
  t = np.array(rec.time)
  channels = {}
  for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    channels[lbl] = np.array (rec.analog[i])

  # display the channels in groups of three
  labels = [lbl for lbl in channels]
  fig, ax = plt.subplots(2, 1, sharex = 'col', figsize=(12,8), constrained_layout=True)
  fig.suptitle ('Case: ' + root)
  for i in range(2):
    for j in range(3):
      lbl = labels[3*i + j]
      ax[i].plot(t, channels[lbl], label=lbl)
    ax[i].grid()
    ax[i].legend()

  plt.show()

