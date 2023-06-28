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
  total_days = 3
  write_daily_output = False
  sys_name = 'uc_case'
  load_scale = 1.0
  if len(sys.argv) > 1:
    load_scale = float(sys.argv[1])
  d = mpow.read_matpower_casefile ('{:s}.m'.format (sys_name))
#  mpow.summarize_casefile (d, 'Input')

  # set up the case and loads for day 1
  # assume all units have been on for 24 hours to start, so MOST can leave them on or switch them off without restriction
  unit_states = np.ones(len(d['gen'])) * 24.0
  fixed_load, responsive_load = mpow.ercot_daily_loads (start=0, end=24, resp_scale=1.0/3.0)
  mpow.write_unresponsive_load_profile ('uc_unresp', mpow.ercot8_load_rows, fixed_load[:,:24], load_scale)
  mpow.write_responsive_load_profile ('uc_resp', mpow.ercot8_load_rows, responsive_load[:,:24], load_scale, 'uc_unresp')
  fscript, fsummary = mpow.write_most_solve_file ('uc')

  total_f = 0.0
  total_Pg = None
  total_Pd = None
  total_Pf = None
  total_u = None
  total_lamP = None
  total_muF = None

  # loop over 3 days, changing the wind and unit_states for each one
  for day in range(total_days):
    start = day * 24
    end = start + 24
    wind = mpow.ercot_wind_profile ('wind_plants.dat', start, end)
    mpow.write_wind_profile ('uc_wind', mpow.ercot8_wind_plant_rows, wind[:,:24])
    mpow.write_xgd_function ('uc_xgd', d['gen'], d['gencost'], d['genfuel'], unit_states)
    print ('Running {:s} and saving results to {:s} for day {:d}, hours {:d}-{:d}'.format (fscript, fsummary, day+1, start, end))
    mpow.run_matpower_and_wait (fscript)

    # analyze day 1
    f, nb, ng, nl, ns, nt, nj_max, nc_max, Pg, Pd, Pf, u, lamP, muF = mpow.read_most_solution(fsummary)
    print ('*** f={:.4e} on day {:d}'.format(f, day+1))
    total_f += f
    total_Pg = mpow.concatenate_MOST_result (total_Pg, Pg)
    total_Pd = mpow.concatenate_MOST_result (total_Pd, Pd)
    total_Pf = mpow.concatenate_MOST_result (total_Pf, Pf)
    total_u = mpow.concatenate_MOST_result (total_u, u)
    total_lamP = mpow.concatenate_MOST_result (total_lamP, lamP)
    total_muF = mpow.concatenate_MOST_result (total_muF, muF)
    # update the generator cumulative up/down times for next day's solution
    for i in range(ng):
      unit_states[i] = mpow.update_unit_state (unit_states[i], u[i])
  # print ('nb={:d}, ng={:d}, nl={:d}, ns={:d}, nt={:d}, nj_max={:d}, nc_max={:d}'.format(nb, ng, nl, ns, nt, nj_max, nc_max))
  # print ('Pg', np.shape(Pg), Pg.dtype)
  # print ('Pd', np.shape(Pd), Pd.dtype)
  # print ('Pf', np.shape(Pf), Pf.dtype)
  # print ('u', np.shape(u), u.dtype)
  # print ('lamP', np.shape(lamP), lamP.dtype)
  # print ('muF', np.shape(muF), muF.dtype)

    if write_daily_output:
      mpow.write_most_summary (d, lamP, Pf, muF, unit_states, u)

  print ('\n\nFinished simulation of {:d} days, total f = {:.4e}'.format (total_days, total_f))
  mpow.write_most_summary (d, total_lamP, total_Pf, total_muF, unit_states, total_u, show_hours_run=True)
  np.savetxt ('{:s}_Pg.txt'.format (sys_name), total_Pg)
  np.savetxt ('{:s}_Pd.txt'.format (sys_name), total_Pd)
  np.savetxt ('{:s}_Pf.txt'.format (sys_name), total_Pf)
  np.savetxt ('{:s}_u.txt'.format (sys_name), total_u)
  np.savetxt ('{:s}_lamP.txt'.format (sys_name), total_lamP)
  np.savetxt ('{:s}_muF.txt'.format (sys_name), total_muF)

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


