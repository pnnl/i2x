# Copyright (C) 2020-2023 Battelle Memorial Institute
# file: cat_most.py
# concatenates MOST solutions and saves to numpy arrays

import numpy as np
import i2x.mpow_utilities as mpow

if __name__ == '__main__':
  summaries = ['msout_day1_dcpf.txt', 'msout_day2_dcpf.txt', 'msout_day3_dcpf.txt']
  sys_name = 'test_case'

  d = mpow.read_matpower_casefile ('{:s}.m'.format(sys_name))
  ng = len(d['gen'])

  total_f = 0.0
  total_Pg = None
  total_Pd = None
  total_Pf = None
  total_u = None
  total_lamP = None
  total_muF = None
  unit_states = np.ones(ng) * 24.0

  for fname in summaries:
    f, nb, ng, nl, ns, nt, nj_max, nc_max, psi, Pg, Pd, Rup, Rdn, SoC, Pf, u, lamP, muF = mpow.read_most_solution(fname)
    print ('f={:.4e} from {:s}'.format(f, fname))
    total_f += f
    total_Pg = mpow.concatenate_MOST_result (total_Pg, Pg)
    total_Pd = mpow.concatenate_MOST_result (total_Pd, Pd)
    total_Pf = mpow.concatenate_MOST_result (total_Pf, Pf)
    total_u = mpow.concatenate_MOST_result (total_u, u)
    total_lamP = mpow.concatenate_MOST_result (total_lamP, lamP)
    total_muF = mpow.concatenate_MOST_result (total_muF, muF)
    for i in range(ng):
      unit_states[i] = mpow.update_unit_state (unit_states[i], u[i])

  print ('\n\nFinished concatenation of {:d} days, total f = {:.4e}'.format (len(summaries), total_f))
  mpow.write_most_summary (d, total_lamP, total_Pf, total_muF, unit_states, total_u, show_hours_run=True)
  np.savetxt ('{:s}_Pg.txt'.format (sys_name), total_Pg)
  np.savetxt ('{:s}_Pd.txt'.format (sys_name), total_Pd)
  np.savetxt ('{:s}_Pf.txt'.format (sys_name), total_Pf)
  np.savetxt ('{:s}_u.txt'.format (sys_name), total_u)
  np.savetxt ('{:s}_lamP.txt'.format (sys_name), total_lamP)
  np.savetxt ('{:s}_muF.txt'.format (sys_name), total_muF)

