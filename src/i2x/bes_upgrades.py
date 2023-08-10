# Copyright (C) 2023 Battelle Memorial Institute
# file: bes_upgrades.py
# from a saved HCA solution, estimates the limiting branch upgrades

import sys
import numpy as np
import i2x.mpow_utilities as mpow
import json
import math

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

def get_default_transformer_mva (kv):
  if kv <= 121.0:
    return 100.0
  elif kv <= 145.0:
    return 200.0
  elif kv <= 242.0:
    return 400.0
  elif kv <= 362.0:
    return 800.0
  elif kv <= 550.0:
    return 1200.0
  return -1.0 # force an error

def reset_mva (d, i, mva):
  newval = '{:.2f}'.format(mva)
  d['branch'][i][mpow.RATE_A] = newval
  d['branch'][i][mpow.RATE_B] = newval
  d['branch'][i][mpow.RATE_C] = newval

def estimate_overhead_line_length (x, kv):
  if kv > 242.0:
    return x / 0.6
  return x / 0.8

def estimate_overhead_lines_in_parallel (z, kv):
  zsurge = 400.0
  if kv > 242.0:
    zsurge = 300.0
  npar = int (0.5 + zsurge / z)
  if npar < 1:
    npar = 1
  return npar

def estimate_transformers_in_parallel (mva, kv):
  npar = int (0.5 + mva / get_default_transformer_mva(kv))
  if npar < 1:
    npar = 1
  return npar

def get_parallel_branch_scale (npar):
  if npar > 1:
    return 1.0 / float(npar)
  return 0.0

def get_branch_description (branch, bus, i):
  desc = '??'
  bus1 = int(branch[i,mpow.F_BUS])
  bus2 = int(branch[i,mpow.T_BUS])
  kv1 = bus[bus1-1,mpow.BASE_KV]
  kv2 = bus[bus2-1,mpow.BASE_KV]
  if kv1 > 100.0 and kv2 > 100.0:
    xpu = branch[i,mpow.BR_X]
    if branch[i,mpow.TAP] > 0.0:
      mva = 100.0 * 0.10 / xpu
      desc = 'Xfmr {:3d}-{:3d} {:7.2f} / {:7.2f} kV x={:.4f}, mva={:.2f}'.format (bus1, bus2, kv1, kv2, xpu, mva)
    elif xpu > 0.0:
      bpu = branch[i,mpow.BR_B]
      npar = 1
      if bpu > 0.0:
        zbase = kv1*kv1/100.0
        x = xpu*zbase
        xc = zbase / branch[i,mpow.BR_B]
        z = math.sqrt(x * xc)
        npar = estimate_overhead_lines_in_parallel (z, kv1)
      mva = npar * get_default_line_mva (kv1)
      # TODO: need a test for overhead vs cable
      miles = estimate_overhead_line_length (x*npar, kv1)
      desc = 'Line {:3d}-{:3d} {:7.2f} kV x={:.4f}, z={:6.2f} ohms, npar={:d}, mva={:.2f}, mi={:.2f}'.format (bus1, bus2, kv1, xpu, z, npar, mva, miles)
    elif xpu < 0.0:
      mva = get_default_line_mva (kv1)
      desc = 'Scap {:3d}-{:3d} {:7.2f} kV x={:.4f}, mva={:.2f}'.format (bus1, bus2, kv1, xpu, mva)
  return desc

def set_estimated_branch_ratings (matpower_dictionary, branch_contingencies=None, contingency_mva_threshold=100.0):
  bus = np.array (matpower_dictionary['bus'], dtype=float)
  branch = np.array (matpower_dictionary['branch'], dtype=float)
  nb = len(bus)
  nl = len(branch)

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
        npar = estimate_transformers_in_parallel (mva, max(kv1, kv2))
        scale = get_parallel_branch_scale (npar)
        reset_mva (matpower_dictionary, i, mva)
      elif xpu > 0.0:
        bpu = branch[i,mpow.BR_B]
        npar = 1
        if bpu > 0.0:
          zbase = kv1*kv1/100.0
          x = xpu*zbase
          xc = zbase / branch[i,mpow.BR_B]
          z = math.sqrt(x * xc)
          npar = estimate_overhead_lines_in_parallel (z, kv1)
          scale = get_parallel_branch_scale (npar)
        mva = npar * get_default_line_mva (kv1)
        reset_mva (matpower_dictionary, i, mva)
      elif xpu < 0.0: # not considering series capacitors in parallel, which is valid for the WECC 240-bus model
        mva = get_default_line_mva (kv1)
        reset_mva (matpower_dictionary, i, mva)
      if branch_contingencies is not None:
        if mva >= contingency_mva_threshold:
          branch_contingencies.append({'branch':i+1, 'scale':scale})
#          print ('contingency {:s}'.format (get_branch_description (branch, bus, i)))

#TODO: need functions that:
#  1) return a dictionary of the limiting branches and their parameters, def get_limiting_branches (case_file, results_file):
#  2) return branch parameters by index, def get_branch_attributes (case_file, idx):
def print_limiting_branches (case_file, results_file):
  d = mpow.read_matpower_casefile (case_file)
  branch = np.array (d['branch'], dtype=float)
  bus = np.array (d['bus'], dtype=float)

  lp = open (results_file).read()
  r = json.loads(lp)
  print (' Bus   HC[GW]')
  for key, val in r['buses'].items():
    print ('{:4d} {:8.3f}'.format (int(key), val['fuels']['hca']))
    i_max = val['max_max_muF']['branch']
    mu_max = val['max_max_muF']['muF']
    i_mean = val['max_mean_muF']['branch']
    mu_mean = val['max_mean_muF']['muF']
    print ('       Max Mu Branch: {:4d} ({:8.3f}) {:s}'.format (i_max, mu_max, 
                                                                get_branch_description (branch, bus, i_max)))
    print ('      Mean Mu Branch: {:4d} ({:8.3f}) {:s}'.format (i_mean, mu_mean, 
                                                                get_branch_description (branch, bus, i_mean)))

