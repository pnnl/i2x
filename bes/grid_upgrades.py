# Copyright (C) 2023 Battelle Memorial Institute
# file: grid_upgrades.py
# from a saved HCA solution, estimates the limiting branch upgrades

import sys
import numpy as np
import i2x.bes_upgrades as bes
import i2x.mpow_utilities as mpow
import json
import math

if __name__ == '__main__':
  results_file = 'IEEE118_out.json'
  case_file = 'IEEE118_wmva.m'
  if len(sys.argv) > 1:
    if int(sys.argv[1]) > 0:
      results_file = 'WECC240_out.json'
      case_file = 'WECC240_case.m'

  lp = open (results_file).read()
  r = json.loads(lp)

  print (' Bus   Generation by Fuel [MW]')
  print ('    ', ' '.join(['{:>8s}'.format(x) for x in mpow.FUEL_LIST]), ' [Max muF Branch] [Mean muF Branch]')
  for key, val in r['buses'].items():
    fuel_str = ' '.join(['{:8.2f}'.format(1000.0 * val['fuels'][x]) for x in mpow.FUEL_LIST])

    i_max = val['max_max_muF']['branch']
    mu_max = val['max_max_muF']['muF']
    i_mean = val['max_mean_muF']['branch']
    mu_mean = val['max_mean_muF']['muF']
    if mu_max > 0.0:
      branch_str = ' [{:.4f} on {:d}] [{:.4f} on {:d}]'.format (mu_max, i_max, mu_mean, i_mean)
    else:
      branch_str = ''

    print ('{:4d} {:s} {:s}'.format (int(key), fuel_str, branch_str))

  print ('\nBranch Upgrade Suggestions:')
  bes.print_limiting_branches (results_file = results_file, case_file = case_file)

