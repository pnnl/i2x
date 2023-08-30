import math
import numpy as np
import json
import i2x.mpow_utilities as mpow
import i2x.bes_upgrades as bes

#chgtab_name = 'hca_contab'
## due to rounding, 0.8333*6504=5419.783 instead of 5420 MVA for two of the path contingencies
#contingencies = [{'branch':1, 'scale':0.5},
#                 {'branch':2, 'scale':0.8333},
#                 {'branch':3, 'scale':0.5},
#                 {'branch':4, 'scale':0.5},
#                 {'branch':5, 'scale':0.5},
#                 {'branch':6, 'scale':0.5},
#                 {'branch':7, 'scale':0.5},
#                 {'branch':8, 'scale':0.5},
#                 {'branch':9, 'scale':0.8333},
#                 {'branch':10, 'scale':0.5},
#                 {'branch':11, 'scale':0.5},
#                 {'branch':12, 'scale':0.5},
#                 {'branch':13, 'scale':0.6667}
#                 ]
#mpow.write_contab_list (chgtab_name, d, contingencies)

HCA_PMAX = 30000.0
HCA_QMAX = 10000.0
HCA_MIN_BR_CONTINGENCY_MVA = 200.0

if __name__ == '__main__':
  min_kv = 100.0
  mva_upgrades = None
  min_contingency_mva = 2000.0
  sys_name = 'hca'

  cfg = {}
  cfg['case_title'] = 'hca'
  cfg['sys_name'] = sys_name
  cfg['load_scale'] = 2.75
  cfg['upgrades'] = None
  cfg['softlims'] = False
  cfg['glpk_opts'] = None

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
  print ('{:d} of {:d} candidate buses for HCA'.format(len(hca_buses), nb))
  cfg['hca_buses'] = hca_buses

  branch_contingencies = []
  bes.set_estimated_branch_ratings (matpower_dictionary=d, 
                                    branch_contingencies=branch_contingencies, 
                                    contingency_mva_threshold=min_contingency_mva,
                                    min_kv=min_kv)

  print ('{:d} of {:d} size-based branch contingencies'.format(len(branch_contingencies), nl))
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

  # write the branch contingency table for size-based filtering - MAY BE OVERWRITTEN with bus contingencies
  chgtab_name = 'hca_contab'
  mpow.write_contab_list (chgtab_name, d, branch_contingencies)

  # find the adjacency-based contingencies for each bus under consideration
  G = bes.build_matpower_graph (d)
  # exclude contingencies that are already in the size-based list
  size_contingencies = []
  for ct in branch_contingencies:
    size_contingencies.append (ct['branch'])
  print (size_contingencies)
  cfg['bus_contingencies'], removals, ncmax = bes.add_bus_contingencies (G, hca_buses, size_contingencies, bLog=False)
  print ('Maximum number of adjacent-bus contingencies is {:d}'.format (ncmax))
  if len(removals) > 0:
    print ('** These HCA candidate buses are radial and do not have a parallel circuit connection:', removals)

  # write the hosting capacity base case, including a new hca generator and fuel-dependent linear generator costs
#  %% bus  Pg     Qg    Qmax     Qmin   Vg  mBase status     Pmax   Pmin  Pc1 Pc2 Qc1min  Qc1max  Qc2min  Qc2max  ramp_agc  ramp_10 ramp_30 ramp_q  apf
#   1.0     0.0  0.0 10000.0 -10000.0  1.0   1000.0  0.0  30000.0     0.0  0.0  0.0  0.0  0.0  0.0  0.0  Inf Inf Inf Inf  0.0;
# gencost = 2.0 10.0 10.0  2.0   0.51   5.0;
  d['gen'].append (np.array([1.0,0.0,0.0,HCA_QMAX,-HCA_QMAX,1.0,1000.0,0.0,HCA_PMAX,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]))
  d['gentype'].append('DL')
  d['genfuel'].append('hca')
  d['gencost'].append(mpow.get_hca_gencosts('hca'))
  # skip this back-filling of default costs, because the base case had ERCOT generator costs from the APEN paper
# ng = len(d['gen'])
# for i in range(ng):
#   d['gencost'][i] = mpow.get_hca_gencosts(d['genfuel'][i])
  print ('Writing the hosting capacity analysis base case to hca_case.m')

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

