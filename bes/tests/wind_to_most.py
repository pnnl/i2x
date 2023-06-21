# Copyright (C) 2021-2023 Battelle Memorial Institute
# file: wind_to_most.py
# converts output from 5 synthetic wind plants to a MOST profile function

import numpy as np
import mpow_utilities as mpow

if __name__ == '__main__':
  hours = 24
  wind_plants = np.array ([99.8, 1657.0, 2242.2, 3562.2, 8730.3])
  row_list = [14, 15, 16, 17, 18]

  # read the LARIMA model profiles, col0=hour, col1..n=MW output
  np.set_printoptions(precision=3)
  dat = np.loadtxt ('wind_plants.dat', delimiter=',')
  print('data shape', np.shape(dat))

  fp = open('test_damwind.m', 'w')
  print('function wind = test_damwind', file=fp)
  mpow.write_most_table_indices(fp)
  print("""  wind = struct( ...
  'type', 'mpcData', ...
  'table', CT_TGEN, ...
  'rows', {:s}, ...
  'col', PMAX, ...
  'chgtype', CT_REP, ...
  'values', [] );""".format(str(row_list)), file=fp)
  for i in range(5):
    colnum = i+1
    rownum = row_list[i]
    vals = str([round(v, 2) for v in dat[:hours,colnum]])
    mvals = vals.replace(',', ';')
    print("""  wind.values(:, 1, {:d}) = {:s};""".format(colnum, mvals), file=fp)
  print('end', file=fp)
  fp.close()



