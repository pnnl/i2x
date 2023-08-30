# Copyright (C) 2017-2023 Battelle Memorial Institute
# file: bes_hca.py
"""Runs a systematic N-1 hosting capacity analysis for each bus, configured in a JSON file.

"""

import sys
import numpy as np
import i2x.mpow_utilities as mpow
import json
import os
import math

def cfg_assign (cfg, tag, val):
  if tag in cfg:
    val = cfg[tag]
  return val

def write_json_results_file (out_name, results, log_output):
  fp = open (out_name, 'w')
  if log_output == True:
    print ('Writing HCA results to {:s}'.format(out_name))
  json.dump (results, fp, indent=2)
  fp.close()

def bes_hca (cfg_filename=None, log_output=True, write_json=True, json_frequency=20):
  sys_name = 'hca'
  case_title = 'hca'
  load_scale = 2.75
  hca_buses = None
  upgrades = None
  branch_contingencies = None
  bus_contingencies = None
  softlims = False
  glpk_opts = None
  if cfg_filename is not None:
    fp = open (cfg_filename, 'r')
    cfg = json.loads(fp.read())
    fp.close()
    sys_name = cfg_assign (cfg, 'sys_name', sys_name)
    case_title = cfg_assign (cfg, 'case_title', case_title)
    load_scale = cfg_assign (cfg, 'load_scale', load_scale)
    hca_buses = cfg_assign (cfg, 'hca_buses', hca_buses)
    upgrades = cfg_assign (cfg, 'upgrades', upgrades)
    softlims = cfg_assign (cfg, 'softlims', softlims)
    glpk_opts = cfg_assign (cfg, 'glpk_opts', glpk_opts)
    branch_contingencies = cfg_assign (cfg, 'branch_contingencies', branch_contingencies)
    bus_contingencies = cfg_assign (cfg, 'bus_contingencies', bus_contingencies)
  out_name = '{:s}_out.json'.format(case_title)
  saved_iteration = 0

  # nominal quantities for the base case, hca generation at zero
  d = mpow.read_matpower_casefile ('{:s}_case.m'.format (sys_name))
  nb = len(d['bus'])
  ng = len(d['gen'])
  nl = len(d['branch'])

  gen = np.array (d['gen'], dtype=float)
  bus = np.array (d['bus'], dtype=float)
  branch = np.array (d['branch'], dtype=float)
  nominalPd = np.sum (bus[:,mpow.PD])
  scaledPd = load_scale * nominalPd
  nominalPmax = np.sum (gen[:,mpow.PMAX])

  # make sure we have a bus list
  if not hca_buses:
    hca_buses = np.arange(1, nb+1, dtype=int)
  if hca_buses[0] < 1:
    hca_buses = np.arange(1, nb+1, dtype=int)
  nhca = len(hca_buses)

  upgrade_name = None
  nupgrades = 0
  if upgrades:
    upgrade_name = '{:s}_upgrades'.format(sys_name)
    nupgrades = len(upgrades)
    mpow.write_contab (upgrade_name, d, upgrades)

  hca_gen_idx = 0

  muFtotal = np.zeros (nl)
  for i in range(ng):
    if d['genfuel'][i] == 'hca':
      hca_gen_idx = i + 1
      nominalPmax -= gen[i,mpow.PMAX]
  nominalPmax *= 0.001
  nominalPd *= 0.001
  scaledPd *= 0.001
  if log_output == True:
    print ('System: {:s} with nominal load={:.3f} GW, actual load={:.3f} GW, existing generation={:.3f} GW'.format(sys_name, nominalPd, scaledPd, nominalPmax))
    print ('HCA generator index = {:d}, load_scale={:.4f}, checking {:d} buses with {:d} grid upgrades'.format(hca_gen_idx, load_scale, nhca, nupgrades))

  results = {'system': sys_name,
             'case_title': case_title,
             'load_scale': load_scale,
             'upgrades': upgrades,
             'buses': {},
             'branches': {}}

  if log_output == True:
    print ('Bus Generation by Fuel[GW]')
    print ('   ', ' '.join(['{:>7s}'.format(x) for x in mpow.FUEL_LIST]), ' [Max muF Branch] [Mean muF Branch] [Local Branch MVA:muF]')
  iteration = 0

  # write the size-based list of branch contingencies, but only if there are no adjacent-bus contingencies
  contab_name = 'hca_contab'
  if branch_contingencies is not None:
    if bus_contingencies is None:
      mpow.write_contab_list (contab_name, d, branch_contingencies)

  for hca_bus in hca_buses:
    iteration += 1
    cmd = 'mpc.gen({:d},1)={:d};'.format(hca_gen_idx, hca_bus) # move the HCA injection to each bus in turn
    fscript, fsummary = mpow.write_hca_solve_file ('hca', load_scale=load_scale, upgrades=upgrade_name, 
                                                   cmd=cmd, quiet=True, glpk_opts=glpk_opts, softlims=softlims)
    # update the list of contingencies for this HCA bus
    if bus_contingencies is not None:
      contingencies = bus_contingencies[str(hca_bus)]
      if branch_contingencies is not None:
        contingencies = contingencies + branch_contingencies
      mpow.write_contab_list (chgtab_name, d, contingencies, bLog=False)

    # remove old results so we know if an error occurred
    if os.path.exists(fsummary):
      os.remove(fsummary)

    mpow.run_matpower_and_wait (fscript, quiet=True)

    if not os.path.exists(fsummary):
      print ('{:3d} ** HCA solution failed at this bus**'.format(hca_bus))
      continue

    f, nb, ng, nl, ns, nt, nj_max, nc_max, psi, Pg, Pd, Rup, Rdn, SoC, Pf, u, lamP, muF = mpow.read_most_solution(fsummary)
    meanPg = np.mean(Pg[:,0,0,:], axis=1)
    meanPd = np.mean(Pd[:,0,0,:], axis=1)
    meanPf = np.mean(Pf[:,0,0,:], axis=1)
    meanlamP = np.mean(lamP[:,0,0,:], axis=1)
    meanmuF = np.mean(muF[:,0,0,:], axis=1)
    baselamP = lamP[:,0,0,0]
    basemuF = muF[:,0,0,0]
    actualPd = np.sum(np.mean(Pd[:,0,0,:], axis=1))
    meanPgen = np.mean(Pg[:,0,0,:], axis=1)
    actualPgen = np.sum(meanPgen)

    # summarize the generation by fuel type
    fuel_Pg = {}
    for fuel in mpow.FUEL_LIST:
      fuel_Pg[fuel] = 0.0
    for i in range(ng):
      fuel = d['genfuel'][i]
      fuel_Pg[fuel] += meanPgen[i]
    for fuel in mpow.FUEL_LIST:
      fuel_Pg[fuel] *= 0.001
    fuel_str = ' '.join(['{:7.3f}'.format(fuel_Pg[x]) for x in mpow.FUEL_LIST])

    # identify the most limiting branches, based on shadow prices
    branch_str = 'None'
    max_max_muF = 0.0
    max_mean_muF = 0.0
    max_i = -1
    mean_i = -1
    for i in range(nl):
      max_val = np.max (muF[i,:,:,:])
      mean_val = np.mean (muF[i,:,:,:])
      if max_val > max_max_muF:
        max_i = i
        max_max_muF = max_val
      if mean_val > max_mean_muF:
        mean_i = i
        max_mean_muF = mean_val
    if max_i >= 0:
      branch_str = ' [{:.4f} on {:d}] [{:.4f} on {:d}]'.format (max_max_muF, max_i+1, max_mean_muF, mean_i+1)

    # check lines to adjacent buses
    bus_str = ''
    local_branches_mu_max = {}
    if bus_contingencies is not None:
      for cd in bus_contingencies[str(hca_bus)]:
        ibr = cd['branch']
        scale = cd['scale']
        rating = branch[ibr-1][mpow.RATE_A]
        mu_max = np.max (muF[ibr-1,:,:,:])
        if mu_max > 0.0:
          bus_str = bus_str + ' {:d}:{:.3f}:{:.6f}'.format (ibr, rating, mu_max)
          local_branches_mu_max[ibr] = mu_max
#       pf = branch[ibr-1][mpow.PF]
#       qf = branch[ibr-1][mpow.QF]
#       pt = branch[ibr-1][mpow.PT]
#       qt = branch[ibr-1][mpow.QT]
#       sf = math.sqrt(pf+pf + qf*qf)
#       st = math.sqrt(pt+pt + qt*qt)
#       mva = max(sf, st)
#       bus_str = bus_str + ' {:d}:{.3f}'.format (ibr, mva/rating)

    if log_output == True:
      print ('{:3d} {:s} {:s} [{:s}]'.format(hca_bus, fuel_str, branch_str, bus_str))

    muFtotal += meanmuF

    # archive the results for post-processing
    results['buses'][int(hca_bus)] = {'fuels':fuel_Pg, 
                                 'max_max_muF':{'branch':max_i+1, 'muF':max_max_muF}, 
                                 'max_mean_muF':{'branch':mean_i+1, 'muF':max_mean_muF},
                                 'local_branches_mu_max':local_branches_mu_max}
    if write_json == True and (iteration % json_frequency == 0):
      write_json_results_file (out_name, results, log_output)
      saved_iteration = iteration

  muFtotal /= nb
  if log_output == True:
    print ('Branches At Limit:')
    print (' idx From   To     muF     MVA     kV1     kV2')
  for i in range(nl):
    if muFtotal[i] > 0.0:
      rating = branch[i][mpow.RATE_A]
      fbus = int(branch[i][mpow.F_BUS])
      tbus = int(branch[i][mpow.T_BUS])
      kv1 = bus[fbus-1][mpow.BASE_KV]
      kv2 = bus[tbus-1][mpow.BASE_KV]
      if log_output == True:
        print ('{:4d} {:4d} {:4d} {:7.4f} {:7.2f} {:7.2f} {:7.2f}'.format(i+1, fbus, tbus, muFtotal[i], rating, kv1, kv2))
      results['branches'][i+1] = {'from':fbus, 'to':tbus, 'muF':muFtotal[i], 'rating':rating, 'kv1':kv1, 'kv2':kv2}

  # The branch results are always going to be newer than bus results inside the loop,
  # so the iteration count does not indicate whether the json file needs to be updated.
  if write_json == True: # and iteration > saved_iteration:
    write_json_results_file (out_name, results, log_output)
  return results

