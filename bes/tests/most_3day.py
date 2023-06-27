import sys
import math
import numpy as np
import mpow_utilities as mpow

# some data and utilities from CIMHub/BES/mpow.py

FUELS = {
  'hydro':  {'c2':1.0e-5, 'c1': 1.29, 'c0': 0.0},
  'wind':   {'c2':1.0e-5, 'c1': 0.01, 'c0': 0.0},
  'solar':  {'c2':1.0e-5, 'c1': 0.01, 'c0': 0.0},
  'coal':   {'c2':0.0009, 'c1': 19.0, 'c0': 2128.0},
  'ng':     {'c2':0.0060, 'c1': 45.0, 'c0': 2230.0},
  'nuclear':{'c2':0.00019, 'c1': 8.0, 'c0': 1250.0}
}

# global constants
SQRT3 = math.sqrt(3.0)
RAD_TO_DEG = 180.0 / math.pi
MVA_BASE = 100.0

def get_gencosts(fuel):
  c2 = 0.0
  c1 = 0.0
  c0 = 0.0
  if fuel in FUELS:
    c2 = FUELS[fuel]['c2']
    c1 = FUELS[fuel]['c1']
    c0 = FUELS[fuel]['c0']
  return c2, c1, c0

if __name__ == '__main__':
  sys_name = 'test_case'
  load_scale = 1.0
  if len(sys.argv) > 1:
    load_scale = float(sys.argv[1])
  d = mpow.read_matpower_casefile ('{:s}.m'.format (sys_name))
#  mpow.summarize_casefile (d, 'Input')

  # set up and run day 1
# unit_states = np.ones(len(d['gen'])) * 24.0
# mpow.write_xgd_function ('uc_xgd', d['gen'], d['gencost'], d['genfuel'], unit_states)
# fixed_load, responsive_load = mpow.ercot_daily_loads (start=0, end=24, resp_scale=1.0/3.0)
# wind = mpow.ercot_wind_profile ('wind_plants.dat', 0, 24)
# mpow.write_unresponsive_load_profile ('uc_unresp', mpow.ercot8_load_rows, fixed_load[:,:24], load_scale)
# mpow.write_responsive_load_profile ('uc_resp', mpow.ercot8_load_rows, responsive_load[:,:24], load_scale, 'uc_unresp')
# mpow.write_wind_profile ('uc_wind', mpow.ercot8_wind_plant_rows, wind[:,:24])
  fscript, fsummary = mpow.write_most_solve_file ('uc')
  print ('Running {:s} and saving results to {:s}'.format (fscript, fsummary))
# mpow.run_matpower_and_wait (fscript)

  # analyze day 1
  f, nb, ng, nl, ns, nt, nj_max, nc_max, Pg, Pd, Pf, u, lamP, muF = mpow.read_most_solution(fsummary)
  print ('f={:.4e}, nb={:d}, ng={:d}, nl={:d}, ns={:d}, nt={:d}, nj_max={:d}, nc_max={:d}'.format(f, nb, ng, nl, ns, nt, nj_max, nc_max))
  print ('Pg', np.shape(Pg), Pg.dtype)
  print ('Pd', np.shape(Pd), Pd.dtype)
  print ('Pf', np.shape(Pf), Pf.dtype)
  print ('u', np.shape(u), u.dtype)
  print ('lamP', np.shape(lamP), lamP.dtype)
  print ('muF', np.shape(muF), muF.dtype)

  bus = d['bus']
  print ('Bus Summary')
  print ('Idx  MaxLMP  AvgLMP')
  for i in range (nb):
    print ('{:3d} {:7.2f} {:7.2f}'.format(i+1, np.max(lamP[i,:]), np.mean(lamP[i,:])))

  br = d['branch']
  print ('Branch Summary')
  print ('Idx Frm  To  Rating  PkFlow Avg muF')
  for i in range (nl):
    print ('{:3d} {:3d} {:3d} {:7.1f} {:7.1f} {:7.2f}'.format(i+1, int(float(br[i][mpow.F_BUS])), int(float(br[i][mpow.T_BUS])), 
                                                              float(br[i][mpow.RATE_A]), np.max(np.abs(Pf[i,:])), 
                                                              np.mean(muF[i,:])))
  gen = d['gen']
  print ('Generator States')
  print ('Idx  At Fuel    Now Fnl History')
  for i in range (ng):
    fnl = mpow.final_unit_state_history (u[i])
    print ('{:3d} {:3d} {:7s} {:3d} {:3d}'.format(i+1, int(float (gen[i][mpow.GEN_BUS])), d['genfuel'][i], int(u[i,-1]), int(fnl)), u[i])

#  quit()

# fscript, fsolved, fsummary = mpow.write_matpower_solve_file (sys_name, load_scale)
# mpow.run_matpower_and_wait (fscript)
# mpow.print_solution_summary (fsummary, details=True)
# r = mpow.read_matpower_casefile (fsolved)
# for tag in ['bus', 'gen', 'branch', 'gencost']:
#   r[tag] = np.array(r[tag], dtype=float)
# mpow.summarize_casefile (r, 'Solved')
# print ('Min and max bus voltages=[{:.4f},{:.4f}]'.format (np.min(r['bus'][:,mpow.VM]),np.max(r['bus'][:,mpow.VM])))
# print ('Load = {:.3f} + j{:.3f} MVA'.format (np.sum(r['bus'][:,mpow.PD]),np.sum(r['bus'][:,mpow.QD])))
# print ('Gen =  {:.3f} + j{:.3f} MVA'.format (np.sum(r['gen'][:,mpow.PG]),np.sum(r['gen'][:,mpow.QG])))
# gen_online = np.array(r['gen'][:,mpow.GEN_STATUS]>0)
# print ('{:d} of {:d} generators on line'.format (int(np.sum(gen_online)),r['gen'].shape[0]))
# pgmax = np.sum(r['gen'][:,mpow.PMAX], where=gen_online)
# qgmax = np.sum(r['gen'][:,mpow.QMAX], where=gen_online)
# qgmin = np.sum(r['gen'][:,mpow.QMIN], where=gen_online)
# print ('Online capacity = {:.2f} MW, {:.2f} to {:.2f} MVAR'.format (pgmax, qgmin, qgmax))


