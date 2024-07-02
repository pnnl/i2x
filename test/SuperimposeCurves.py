# Copyright (C) 2023 Battelle Memorial Institute
# Copyright (C) 2024 Institute of Electrical and Electronic Engineers (IEEE)
# file: SuperimposeCurves.py
"""Plots load and PV daily curves for secondary network example
"""
import matplotlib.pyplot as plt
import numpy as np
import os
plt.rcParams['savefig.directory'] = 'd:/ieee/p1729/drafts/figures' # '../docs/media' # os.getcwd()

if __name__ == "__main__":
  dload = np.loadtxt ('c:/src/i2x/src/i2x/models/support/qdaily.dat')
  dpv = np.loadtxt ('c:/src/i2x/src/i2x/models/support/pclear.dat')
  print ('dload range {:.4f} - {:.4f} in {:d} points'.format (min(dload), max(dload), len(dload)))
  print ('dpv range {:.4f} - {:.4f} in {:d} points'.format (min(dpv), max(dpv), len(dpv)))
  pvbase = max(dpv)
  lbase = max(dload)
  hrs = np.linspace (0.0, 24.0, len(dload))

  fig, ax = plt.subplots (1, 1, sharex = 'col', figsize=(5,4), constrained_layout=True)
  ax.set_title ('Daily Power Curves')
  ax.plot (hrs, dpv / pvbase, color='red', label='PV')
  ax.plot (hrs, dload / lbase, color='blue', label='Load')

  ax.legend()
  ax.grid()
  ax.set_xlim (0.0, 24.0)
  ax.set_xticks ([0, 4, 8, 12, 16, 20, 24])
  ax.set_xlabel ('Hours')
  ax.set_ylabel ('per-unit')

  plt.show()
  plt.close()


