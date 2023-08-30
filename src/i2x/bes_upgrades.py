# Copyright (C) 2023 Battelle Memorial Institute
# file: bes_upgrades.py
# from a saved HCA solution, estimates the limiting branch upgrades

import sys
import numpy as np
import i2x.mpow_utilities as mpow
import networkx as nx
import json
import math

def estimate_substation_position_cost (kv):
  if kv <= 121.0:
    return 1.9e6
  elif kv <= 145.0:
    return 2.0e6
  elif kv <= 242.0:
    return 3.0e6
  elif kv <= 362.0:
    return 5.0e6
  elif kv <= 550.0:
    return 10.0e6
  return -1.0 # force an error

def estimate_capacitor_cost (kv, mvar):
  sub_cost = 1.0 * estimate_substation_position_cost (kv)
  if sub_cost >= 0.0:
    return sub_cost + mvar*11.0e3
  return -1.0 # force an error

# for one circuit, plus two breaker positions
def estimate_line_cost (kv, miles):
  sub_cost = 2.0 * estimate_substation_position_cost (kv)
  if kv <= 121.0:
    return sub_cost + miles*1.9e6
  elif kv <= 145.0:
    return sub_cost + miles*2.0e6
  elif kv <= 242.0:
    return sub_cost + miles*2.1e6
  elif kv <= 362.0:
    return sub_cost + miles*3.5e6
  elif kv <= 550.0:
    return sub_cost + miles*4.0e6
  return -1.0 # force an error

# includes one breaker position in existing substations
def estimate_transformer_cost (kv, mva):
  sub_cost = 1.0 * estimate_substation_position_cost (kv)
  if kv <= 121.0:
    return sub_cost + mva*5.5e3
  elif kv <= 145.0:
    return sub_cost + mva*6.0e3
  elif kv <= 242.0:
    return sub_cost + mva*7.0e3
  elif kv <= 362.0:
    return sub_cost + mva*9.0e3
  elif kv <= 550.0:
    return sub_cost + mva*12.0e3
  return -1.0 # force an error

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
    return 1.0 - 1.0 / float(npar)
  return 0.0

# pass i as zero-based index, not the branch number
def get_branch_description (branch, bus, i, bEstimateMVA=False, bEstimateCost=False):
  desc = '??'
  bus1 = int(branch[i,mpow.F_BUS])
  bus2 = int(branch[i,mpow.T_BUS])
  kv1 = bus[bus1-1,mpow.BASE_KV]
  kv2 = bus[bus2-1,mpow.BASE_KV]
  xpu = branch[i,mpow.BR_X]
  mva = branch[i,mpow.RATE_A]
  if branch[i,mpow.TAP] > 0.0:
    if bEstimateMVA:
      mva = 100.0 * 0.10 / xpu
    desc = 'Xfmr {:3d}-{:3d} {:7.2f} / {:7.2f} kV x={:.4f}, mva={:.2f}'.format (bus1, bus2, kv1, kv2, xpu, mva)
    if bEstimateCost:
      desc = desc + ', ${:.2f}M'.format (estimate_transformer_cost (kv1, mva) / 1.0e6)
  elif xpu > 0.0:
    bpu = branch[i,mpow.BR_B]
    npar = 1
    zbase = kv1*kv1/100.0
    x = xpu*zbase
    z = -1.0
    if bpu > 0.0:
      xc = zbase / branch[i,mpow.BR_B]
      z = math.sqrt(x * xc)
      npar = estimate_overhead_lines_in_parallel (z, kv1)
    if bEstimateMVA:
      mva = npar * get_default_line_mva (kv1)
    # TODO: need a test for overhead vs cable
    miles = estimate_overhead_line_length (x*npar, kv1)
    desc = 'Line {:3d}-{:3d} {:7.2f} kV x={:.4f}, z={:6.2f} ohms, npar={:d}, mva={:.2f}, mi={:.2f}'.format (bus1, bus2, kv1, xpu, z, npar, mva, miles)
    if bEstimateCost:
      desc = desc + ', ${:.2f}M/ckt'.format (estimate_line_cost (kv1, miles) / 1.0e6)
  elif xpu < 0.0:
    if bEstimateMVA:
      mva = get_default_line_mva (kv1)
    desc = 'Scap {:3d}-{:3d} {:7.2f} kV x={:.4f}, mva={:.2f}'.format (bus1, bus2, kv1, xpu, mva)
    if bEstimateCost:
      desc = desc + ', ${:.2f}M'.format (estimate_capacitor_cost (kv1, mva) / 1.0e6)
  return desc

# pass i as zero-based index, not the branch number
def get_branch_next_upgrade (branch, bus, i):
  scale = 0.0
  cost = 0.0
  bus1 = int(branch[i,mpow.F_BUS])
  bus2 = int(branch[i,mpow.T_BUS])
  kv = max (bus[bus1-1,mpow.BASE_KV], bus[bus2-1,mpow.BASE_KV])
  xpu = branch[i,mpow.BR_X]
  mva = branch[i,mpow.RATE_A]
  if branch[i,mpow.TAP] > 0.0:
    newmva = get_default_transformer_mva (kv)
    cost = estimate_transformer_cost (kv, newmva)
  elif xpu > 0.0:
    newmva = get_default_line_mva (kv)
    npar = int (0.5 + mva/newmva) # how many existing lines on this right-of-way
    zbase = kv*kv/100.0
    x = xpu*zbase
    miles = estimate_overhead_line_length (x*npar, kv)
    cost = estimate_line_cost (kv, miles)
  elif xpu < 0.0:
    newmva = get_default_line_mva (kv)
    cost = estimate_capacitor_cost (kv, newmva)
  scale = 1.0 + newmva / mva
  return scale, cost

def estimate_branch_scaling (x, b, tap, kv1, kv2, mva):
  npar = 1
  length = 1.0
  if tap > 0.0:
    eclass = 'xfmr'
    npar = estimate_transformers_in_parallel (mva, max(kv1, kv2))
  elif x >= 0.0:
    eclass = 'line'
    zbase = kv1*kv1/100.0
    x *= zbase
    if b > 0.0:
      xc = zbase / b
      z = math.sqrt(x * xc)
      npar = estimate_overhead_lines_in_parallel (z, kv1)
    length = estimate_overhead_line_length (x*npar, kv1)
  else:
    eclass = 'scap'

  scale = get_parallel_branch_scale (npar)
  return eclass, round (length, 3), npar, round (scale, 6)

def set_estimated_branch_ratings (matpower_dictionary, 
                                  branch_contingencies=None, 
                                  contingency_mva_threshold=100.0, 
                                  contingency_kv_threshold=100.0,
                                  min_kv=10.0):
  bus = np.array (matpower_dictionary['bus'], dtype=float)
  branch = np.array (matpower_dictionary['branch'], dtype=float)
  nb = len(bus)
  nl = len(branch)

  for i in range(nl):
    bus1 = int(branch[i,mpow.F_BUS])
    bus2 = int(branch[i,mpow.T_BUS])
    kv1 = bus[bus1-1,mpow.BASE_KV]
    kv2 = bus[bus2-1,mpow.BASE_KV]
    if kv1 > min_kv and kv2 > min_kv:
      scale = 0.0
      # mva = branch[i,mpow.RATE_A] these are invalid for IEEE118 and WECC240
      xpu = branch[i,mpow.BR_X]
      if branch[i,mpow.TAP] > 0.0:
        mva = 100.0 * 0.10 / xpu
        npar = estimate_transformers_in_parallel (mva, max(kv1, kv2))
        scale = get_parallel_branch_scale (npar)
        reset_mva (matpower_dictionary, i, mva)
#        print ('xfmr {:d}, {:d}-{:d} kv={:.2f}/{:.2f} x={:.5f} mva={:.2f}'.format (i, bus1, bus2, kv1, kv2, xpu, mva))
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
          if kv1 > contingency_kv_threshold and kv2 > contingency_kv_threshold:
            branch_contingencies.append({'branch':i+1, 'scale':scale})
#            print ('contingency {:s} [scale={:.3f}]'.format (get_branch_description (branch, bus, i), scale))

#TODO: need functions that:
#  1) return a dictionary of the limiting branches and their parameters, def get_limiting_branches (case_file, results_file):
#  2) return branch parameters by index, def get_branch_attributes (case_file, idx):
def print_limiting_branches (case_file, results_file):
  d = mpow.read_matpower_casefile (case_file)
  branch = np.array (d['branch'], dtype=float)
  bus = np.array (d['bus'], dtype=float)

  lp = open (results_file).read()
  r = json.loads(lp)
  print (' Bus   HC[MW]')
  for key, val in r['buses'].items():
    print ('{:4d} {:8.2f}'.format (int(key), 1000.0 * val['fuels']['hca']))
    printed = []
    i_max = val['max_max_muF']['branch']
    mu_max = val['max_max_muF']['muF']
    i_mean = val['max_mean_muF']['branch']
    mu_mean = val['max_mean_muF']['muF']
    if mu_max > 0.0 and i_max not in printed:
      print ('       Max Mu Branch: {:4d} ({:8.3f}) {:s}'.format (i_max, mu_max, 
                                                                get_branch_description (branch, bus, i_max-1, bEstimateCost=True)))
      printed.append (i_max)
    if mu_mean > 0.0 and i_mean not in printed:
      print ('      Mean Mu Branch: {:4d} ({:8.3f}) {:s}'.format (i_mean, mu_mean, 
                                                                get_branch_description (branch, bus, i_mean-1, bEstimateCost=True)))
      printed.append (i_mean)
    if 'local_branches_mu_max' in val:
      for str_ibr, mu in val['local_branches_mu_max'].items():
        ibr = int(str_ibr)
        if ibr not in printed:
          printed.append (ibr)
          print ('        Local Branch: {:4d} ({:8.3f}) {:s}'.format (ibr, mu, get_branch_description (branch, bus, ibr-1, bEstimateCost=True)))

def get_graph_bus_type (idx):
  if idx == 1:
    return 'PQ'
  elif idx == 2:
    return 'PV'
  elif idx == 3:
    return 'Swing'
  return 'Isolated'

def build_matpower_graph (d):
  branch = d['branch']
  bus = d['bus']
  G = nx.Graph()
  for i in range(len(bus)):
    n = i+1
    nclass = get_graph_bus_type (bus[i, mpow.BUS_TYPE])
    G.add_node (n, nclass=nclass, ndata={'kV':bus[i, mpow.BASE_KV], 'PD':bus[i, mpow.PD], 'QD': bus[i, mpow.QD]})
  for i in range(len(branch)):
    n1 = int (branch[i, mpow.F_BUS])
    n2 = int (branch[i, mpow.T_BUS])
    kV1 = bus[n1-1, mpow.BASE_KV]
    kV2 = bus[n2-1, mpow.BASE_KV]
    MVA = branch[i, mpow.RATE_A]
    r = branch[i, mpow.BR_R]
    x = branch[i, mpow.BR_X]
    b = branch[i, mpow.BR_B]
    tap = branch[i, mpow.TAP]
    # now estimate how many parallel branches this represents, and the line length if applicable
    eclass, length, npar, scale = estimate_branch_scaling (x, b, tap, kV1, kV2, MVA)
    G.add_edge (n1, n2, eclass=eclass, ename=str(i+1), 
                edata={'kV1':kV1, 'kV2':kV2, 'MVA':MVA, 'r':r, 'x':x, 'b':b, 'tap':tap, 'npar':npar, 'miles':length, 'scale':scale}, 
                weight=x)
  return G

def add_bus_contingencies (G, hca_buses, size_contingencies=[], bLog=True,
                           contingency_mva_threshold=100.0, 
                           contingency_kv_threshold=100.0):
  d = {}
  ncmax = 0
  removals = []
  for key in hca_buses:
    bus = int(key)
    d[bus] = []
    ev = list(G.edges(nbunch=bus, data=True))
    nc = len(ev)
    if nc > ncmax:
      ncmax = nc
    bExcluded = False
    if nc < 2:
      if ev[0][2]['edata']['npar'] < 2:
        bExcluded = True
        removals.append(bus)
        if bLog:
          print ('** Radial bus {:d} has no parallel circuit and can only serve local load. Might exclude from HCA.'.format (bus))
    if not bExcluded:
      for br in ev:
        edata = br[2]['edata']
        if edata['MVA'] >= contingency_mva_threshold and edata['kV1'] >= contingency_kv_threshold and edata['kV2'] >= contingency_kv_threshold:
          brnum = int(br[2]['ename'])
          if brnum not in size_contingencies:
            scale = br[2]['edata']['scale']
            d[bus].append ({'branch': brnum, 'scale': scale})
  if bLog:
    print ('Maximum number of adjacent-bus contingencies is {:d}'.format (ncmax))
  return d, removals, ncmax

def rebuild_contingencies (mpd, G, poc, min_mva=100.0, min_kv=100.0):
  s = []
  bus = mpd['bus']
  branch = mpd['branch']
  nl = len(branch)
  # size-based contingencies
  for i in range(nl):
    bus1 = int(branch[i,mpow.F_BUS])
    bus2 = int(branch[i,mpow.T_BUS])
    kv = min(bus[bus1-1,mpow.BASE_KV], bus[bus2-1,mpow.BASE_KV])
    mva = branch[i,mpow.RATE_A]
    if kv >= min_kv and mva >= min_mva:
      if branch[i,mpow.TAP] > 0.0:
        outage = get_default_transformer_mva (kv)
      else:
        outage = get_default_line_mva (kv)
      scale = (mva - outage) / mva
      if scale < 0.01:
        scale = 0.0
      s.append({'branch':i+1, 'scale':scale})

  # bus-based contingencies
  exclusions = []
  for ct in s:
    exclusions.append (ct['branch'])
  b, _, _ = add_bus_contingencies (G, [poc], exclusions, False, min_mva, min_kv)

  return s+b[poc]
