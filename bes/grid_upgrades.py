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
    flag = int(sys.argv[1])
    if flag == 1:
      results_file = 'WECC240_out.json'
      case_file = 'WECC240_wmva.m'
    elif flag == 2:
      results_file = 'IEEE39_out.json'
      case_file = 'IEEE39_wmva.m'

  lp = open (results_file).read()
  r = json.loads(lp)

  print (' Bus   Generation by Fuel [MW]')
  print ('    ', ' '.join(['{:>8s}'.format(x) for x in mpow.FUEL_LIST]))
  for key, val in r['buses'].items():
    fuel_str = ' '.join(['{:8.2f}'.format(1000.0 * val['fuels'][x]) for x in mpow.FUEL_LIST])
    print ('{:4d} {:s}'.format (int(key), fuel_str))

  print ('\nBranch Upgrade Suggestions:')
  bes.print_limiting_branches (results_file = results_file, case_file = case_file)

