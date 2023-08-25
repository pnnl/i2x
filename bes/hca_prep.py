import sys
import math
import numpy as np
import json
import i2x.mpow_utilities as mpow
import i2x.bes_upgrades as bes

from bes_cases import *

HCA_PMAX = 30000.0
HCA_QMAX = 10000.0
HCA_MIN_BR_CONTINGENCY_MVA = 200.0

if __name__ == '__main__':
  case_id = 0
  if len(sys.argv) > 1:
    case_id = int(sys.argv[1])
  sys_name = CASES[case_id]['name']
  load_scale = CASES[case_id]['load_scale']
  min_kv = CASES[case_id]['min_kv_to_upgrade']
  mva_upgrades = CASES[case_id]['mva_upgrades']
  min_contingency_mva = CASES[case_id]['min_contingency_mva']

  cfg = {}
  cfg['case_title'] = sys_name
  cfg['sys_name'] = 'hca'
  cfg['load_scale'] = load_scale
  cfg['upgrades'] = None

  d = mpow.read_matpower_casefile ('{:s}.m'.format (sys_name))
  nb = len(d['bus'])
  ng = len(d['gen'])
  nl = len(d['branch'])

  gen = np.array (d['gen'], dtype=float)
  bus = np.array (d['bus'], dtype=float)
  branch = np.array (d['branch'], dtype=float)

  hca_buses = []
  for i in range(nb):
    if bus[i,mpow.BASE_KV] > 100.0:
      hca_buses.append (int(bus[i,mpow.BUS_I]))
  print ('{:d} of {:d} buses for HCA'.format(len(hca_buses), nb))
  cfg['hca_buses'] = hca_buses

  branch_contingencies = []
  bes.set_estimated_branch_ratings (matpower_dictionary=d, 
                                    branch_contingencies=branch_contingencies, 
                                    contingency_mva_threshold=min_contingency_mva,
                                    min_kv=min_kv)

  print ('{:d} of {:d} branch contingencies'.format(len(branch_contingencies), nl))
  cfg['branch_contingencies'] = branch_contingencies

  if mva_upgrades is not None:
    for row in mva_upgrades:
      idx = row['branch_number'] - 1
      d['branch'][idx][mpow.RATE_A] = row['new_mva']
      d['branch'][idx][mpow.RATE_B] = row['new_mva']
      d['branch'][idx][mpow.RATE_C] = row['new_mva']
      print ('Upsizing branch MVA', idx+1, d['branch'][idx])

  wmva_name = '{:s}_wmva'.format(sys_name)
  print ('Writing base case updates to {:s}.m'.format(wmva_name))
  mpow.write_matpower_casefile (d, wmva_name)

  # write the branch contingency table
  chgtab_name = 'hca_contab'
  mpow.write_contab_list (chgtab_name, d, branch_contingencies)

  # write the hosting capacity base case, including a new hca generator and fuel-dependent linear generator costs
#  %% bus  Pg     Qg    Qmax     Qmin   Vg  mBase status     Pmax   Pmin  Pc1 Pc2 Qc1min  Qc1max  Qc2min  Qc2max  ramp_agc  ramp_10 ramp_30 ramp_q  apf
#   1.0     0.0  0.0 10000.0 -10000.0  1.0   1000.0  0.0  30000.0     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
# gencost = 2.0 10.0 10.0  2.0   0.51   5.0;
  d['gen'].append (np.array([1.0,0.0,0.0,HCA_QMAX,-HCA_QMAX,1.0,1000.0,0.0,HCA_PMAX,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]))
  d['gentype'].append('DL')
  d['genfuel'].append('hca')
  d['gencost'].append(mpow.get_hca_gencosts('hca'))
  ng = len(d['gen'])
  for i in range(ng):
    d['gencost'][i] = mpow.get_hca_gencosts(d['genfuel'][i])
  print ('Writing the hosting capacity analysis base case to hca_case.m')
  # write the branch contingency table and extra generator data (xgd) for matpower
  chgtab_name = 'hca_contab'
  mpow.write_contab_list (chgtab_name, d, branch_contingencies)

  # extra generator data (xgd) including the new one for HCA
  # assume all units have been on for 24 hours to start, so MOST can leave them on or switch them off without restriction
  unit_states = np.ones(len(d['gen'])) * 24.0
  mpow.write_xgd_function ('hca_xgd', d['gen'], d['gencost'], d['genfuel'], unit_states)
  mpow.write_matpower_casefile (d, 'hca_case')

  cfg_name = '{:s}_prep.json'.format(sys_name)
  fp = open (cfg_name, 'w')
  print ('Writing HCA buses and contingencies to {:s}'.format(cfg_name))
  json.dump (cfg, fp, indent=2)
  fp.close()

