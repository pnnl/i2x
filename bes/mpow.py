import sys
import os
import math
import subprocess
import numpy as np
import i2x.mpow_utilities as mpow

# some data from CIMHub/BES/mpow.py

from bes_cases import *

# global constants
SQRT3 = math.sqrt(3.0)
RAD_TO_DEG = 180.0 / math.pi
MVA_BASE = 100.0

# sample code from TESP that automates Matpower in Octave
# https://github.com/pnnl/tesp/blob/develop/examples/capabilities/ercot/case8/tso_most.py

def write_solve_file (root, load_scale):
  fscript = 'solve{:s}.m'.format(root)
  fsolved = '{:s}solved.m'.format(root)
  fsummary = '{:s}summary.txt'.format(root)
  fp = open (fscript, 'w')
  print ("""clear;""", file=fp)
  print ("""cd {:s}""".format (os.getcwd()), file=fp)
  print ("""mpc = loadcase({:s});""".format (root.upper()), file=fp)
  print ("""mpc = scale_load({:.5f},mpc);""".format (load_scale), file=fp)
  print ("""opt1 = mpoption('out.all', 0, 'verbose', 0);""", file=fp)
  print ("""results=runpf(mpc, opt1);""", file=fp)
  print ("""define_constants;""", file=fp)
  print ("""opt2 = mpoption('out.sys_sum', 1, 'out.bus', 0, 'out.branch', 0);""", file=fp)
  print ("""fd = fopen('{:s}', 'w');""".format (fsummary), file=fp)
  print ("""fprintf(fd,'results.success = %d\\n', results.success);""", file=fp)
  print ("""fprintf(fd,'results.iterations = %d\\n', results.iterations);""", file=fp)
  print ("""fprintf(fd,'results.et = %.4f\\n', results.et);""", file=fp)
  print ("""printpf(results, fd, opt2);""", file=fp)
  print ("""fclose(fd);""", file=fp)
  print ("""savecase('{:s}', results);""".format (fsolved), file=fp)
  print ("""exit;""", file=fp)
  fp.close()
  return fscript, fsolved, fsummary

if __name__ == '__main__':
  case_id = 0
  if len(sys.argv) > 1:
    case_id = int(sys.argv[1])
  sys_name = CASES[case_id]['name']
  load_scale = CASES[case_id]['load_scale']
  d = mpow.read_matpower_casefile ('{:s}.m'.format (sys_name))
  mpow.summarize_casefile (d, 'Input')
  fscript, fsolved, fsummary = write_solve_file (sys_name, load_scale)
  mpow.run_matpower_and_wait (fscript)
  mpow.print_solution_summary (fsummary, details=True)
  r = mpow.read_matpower_casefile (fsolved)
  mpow.summarize_casefile (r, 'Solved')
  print ('Min and max bus voltages=[{:.4f},{:.4f}]'.format (np.min(r['bus'][:,mpow.VM]),np.max(r['bus'][:,mpow.VM])))
  print ('Load = {:.3f} + j{:.3f} MVA'.format (np.sum(r['bus'][:,mpow.PD]),np.sum(r['bus'][:,mpow.QD])))
  print ('Gen =  {:.3f} + j{:.3f} MVA'.format (np.sum(r['gen'][:,mpow.PG]),np.sum(r['gen'][:,mpow.QG])))
  gen_online = np.array(r['gen'][:,mpow.GEN_STATUS]>0)
  print ('{:d} of {:d} generators on line'.format (int(np.sum(gen_online)),r['gen'].shape[0]))
  pgmax = np.sum(r['gen'][:,mpow.PMAX], where=gen_online)
  qgmax = np.sum(r['gen'][:,mpow.QMAX], where=gen_online)
  qgmin = np.sum(r['gen'][:,mpow.QMIN], where=gen_online)
  print ('Online capacity = {:.2f} MW, {:.2f} to {:.2f} MVAR'.format (pgmax, qgmin, qgmax))

