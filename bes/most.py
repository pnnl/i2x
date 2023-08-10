import sys
import os
import math
import subprocess
import numpy as np
import i2x.mpow_utilities as mpow
import i2x.bes_upgrades as bes

# some data from CIMHub/BES/mpow.py

CASES = [
  {'id': '1783D2A8-1204-4781-A0B4-7A73A2FA6038', 
   'name': 'IEEE118', 
   'swingbus':'131',
   'load_scale':0.6748},
  {'id': '2540AF5C-4F83-4C0F-9577-DEE8CC73BBB3', 
   'name': 'WECC240', 
   'swingbus':'2438',
   'load_scale':1.0425},
]

if sys.platform == 'win32':
  octave = '"C:\Program Files\GNU Octave\Octave-8.2.0\octave-launch.exe" --no-gui'
else:
  octave = 'octave --no-window-system --no-gui'

def write_local_solve_file (root, load_scale=1.0, quiet=False):
  fscript = 'solve_{:s}.m'.format(root)
  fsummary = '{:s}_summary.txt'.format(root)
  fp = open(fscript, 'w')
  print("""clear;""", file=fp)
  print("""define_constants;""", file=fp)
  print("""mpopt = mpoption('verbose', 0, 'out.all', 0);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.dc_model', 1);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.uc.run', 1);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.solver', 'GLPK');""", file=fp)
  if quiet:
    print("""mpopt = mpoption(mpopt, 'glpk.opts.msglev', 0);""", file=fp)
  else:
    print("""mpopt = mpoption(mpopt, 'glpk.opts.msglev', 1);""", file=fp)
  print("""mpc = loadcase ('{:s}_case.m');""".format(root), file=fp)
  print("""mpc = scale_load({:.5f},mpc);""".format (load_scale), file=fp)
  print("""xgd = loadxgendata('{:s}_xgd.m', mpc);""".format(root), file=fp)
  print("""mdi = loadmd(mpc, [], xgd, []);""", file=fp)
  print("""mdo = most(mdi, mpopt);""", file=fp)
  print("""ms = most_summary(mdo);""", file=fp)
  print("""save('-text', '{:s}', 'ms');""".format(fsummary), file=fp)
  if not quiet:
    print("""total_time = mdo.results.SolveTime + mdo.results.SetupTime""", file=fp)
  fp.close()
  return fscript, fsummary

if __name__ == '__main__':
  case_id = 0
  if len(sys.argv) > 1:
    case_id = int(sys.argv[1])
  sys_name = CASES[case_id]['name']
  load_scale = CASES[case_id]['load_scale']

  d = mpow.read_matpower_casefile ('{:s}.m'.format (sys_name))
  # assign sensible ratings
  bes.set_estimated_branch_ratings (matpower_dictionary=d)
  # assign linear cost functions
  ng = len(d['gen'])
  for i in range(ng):
    d['gencost'][i] = mpow.get_hca_gencosts(d['genfuel'][i])
  # Write extra generator data (xgd), assuming all units have been on for 24 hours to start, 
  # so MOST can leave them on or switch them off without restriction
  unit_states = np.ones(len(d['gen'])) * 24.0
  mpow.write_xgd_function ('most_xgd', d['gen'], d['gencost'], d['genfuel'], unit_states)

  # write the modified Matpower case with attributes customized for MOST
  mpow.write_matpower_casefile (d, 'most_case')

  # run the MOST case
  fscript, fsummary = write_local_solve_file ('most', load_scale=load_scale)
  mpow.run_matpower_and_wait (fscript, quiet=False)
  f, nb, ng, nl, ns, nt, nj_max, nc_max, psi, Pg, Pd, Rup, Rdn, SoC, Pf, u, lamP, muF = mpow.read_most_solution(fsummary)
  print ('MOST cost = {:.2f}'.format (f))



