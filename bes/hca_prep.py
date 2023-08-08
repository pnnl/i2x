import sys
import math
import numpy as np
import json
from tests import mpow_utilities as mpow

HCA_PMAX = 30000.0
HCA_QMAX = 10000.0
HCA_MIN_BR_CONTINGENCY_MVA = 200.0

def get_default_line_mva (kv):
  if kv <= 121.0:
    return 131.0
  elif kv <= 145.0:
    return 157.0
  elif kv <= 242.0:
    return 600.0
  elif kv <= 362.0:
    return 1084.0
  elif kv <= 550.0:
    return 1800.0
  return -1.0 # force an error

def reset_mva (d, i, mva):
  newval = '{:.2f}'.format(mva)
  d['branch'][i][mpow.RATE_A] = newval
  d['branch'][i][mpow.RATE_B] = newval
  d['branch'][i][mpow.RATE_C] = newval

if __name__ == '__main__':
  sys_name = 'IEEE118'
  if len(sys.argv) > 1:
    sys_name = sys.argv[1]
  cfg = {}
  cfg['sys_name'] = sys_name
  cfg['load_scale'] = 1.0
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
  for i in range(nl):
    bus1 = int(branch[i,mpow.F_BUS])
    bus2 = int(branch[i,mpow.T_BUS])
    kv1 = bus[bus1-1,mpow.BASE_KV]
    kv2 = bus[bus2-1,mpow.BASE_KV]
    if kv1 > 100.0 and kv2 > 100.0:
      scale = 0.0
      # mva = branch[i,mpow.RATE_A] these are invalid for IEEE118 and WECC240
      xpu = branch[i,mpow.BR_X]
      if branch[i,mpow.TAP] > 0.0:
        mva = 100.0 * 0.10 / xpu
        reset_mva (d, i, mva)
        #print ('Xfmr {:3d}-{:3d} {:7.2f} / {:7.2f} kV x={:.4f}, mva={:.2f}'.format (bus1, bus2, kv1, kv2, xpu, mva))
      elif xpu > 0.0:
        bpu = branch[i,mpow.BR_B]
        npar = 1
        if bpu > 0.0:
          zbase = kv1*kv1/100.0
          x = xpu*zbase
          xc = zbase / branch[i,mpow.BR_B]
          z = math.sqrt(x * xc)
          npar = int (0.5 + 400.0 / z)
          if npar < 1:
            npar = 1
          if npar > 1:
            scale = 1.0 / float(npar)
        mva = npar * get_default_line_mva (kv1)
        reset_mva (d, i, mva)
        #print ('Line {:3d}-{:3d} {:7.2f} kV x={:.4f}, z={:6.2f} ohms, npar={:d}, mva={:.2f}'.format (bus1, bus2, kv1, xpu, z, npar, mva))
      elif xpu < 0.0:
        mva = get_default_line_mva (kv1)
        reset_mva (d, i, mva)
        #print ('Scap {:3d}-{:3d} {:7.2f} kV x={:.4f}, mva={:.2f}'.format (bus1, bus2, kv1, xpu, mva))
      if mva >= HCA_MIN_BR_CONTINGENCY_MVA:
        branch_contingencies.append({'branch':i+1, 'scale':scale})
  print ('{:d} of {:d} branch contingencies'.format(len(branch_contingencies), nl))
  cfg['branch_contingencies'] = branch_contingencies

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

