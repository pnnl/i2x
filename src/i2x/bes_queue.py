# Copyright (C) 2023 Battelle Memorial Institute
# file: impact.py
"""Simulate a sequence of system impact studies.
"""
import os
import numpy as np
import i2x.bes_hca as hca
import i2x.bes_upgrades as bes
import i2x.mpow_utilities as mpow

HCA_PMAX = 30000.0
HCA_QMAX = 10000.0
MIN_CONT_KV = 100.0
MIN_SIZE_MVA = 100.0
MIN_BUS_MVA = 100.0
bWind = False # alternate addition of wind and solar projects

def reset_queue_defaults ():
  global HCA_PMAX, HCA_QMAX, MIN_CONT_KV, MIN_SIZE_MVA, MIN_BUS_MVA, bWind
  HCA_PMAX = 30000.0
  HCA_QMAX = 10000.0
  MIN_CONT_KV = 100.0
  MIN_SIZE_MVA = 100.0
  MIN_BUS_MVA = 100.0
  bWind = False

def configure_queue (cfg):
  global HCA_PMAX, HCA_QMAX, MIN_CONT_KV, MIN_SIZE_MVA, MIN_BUS_MVA
  base_case = cfg['base_case']
  load_scale = cfg['load_scale']
  reset_queue_defaults ()
  if 'MIN_CONT_KV' in cfg:
    MIN_CONT_KV = cfg['MIN_CONT_KV']
  if 'MIN_SIZE_MVA' in cfg:
    MIN_SIZE_MVA = cfg['MIN_SIZE_MVA']
  if 'MIN_BUS_MVA' in cfg:
    MIN_BUS_MVA = cfg['MIN_BUS_MVA']
  if 'HCA_PMAX' in cfg:
    HCA_PMAX = cfg['HCA_PMAX']
  if 'HCA_QMAX' in cfg:
    HCA_QMAX = cfg['HCA_QMAX']
  return base_case, load_scale

def update_poc_cluster (cluster, app):
  cluster['mw'] += app['mw']
  cluster['costlim'] += app['costlim']
  cluster['itlim'] = max (cluster['itlim'], app['itlim'])
  cluster['apps'].append (app)

def form_clusters (napps=3, poc_list=[15], min_mw=500.0, max_mw=500.0, min_dollars_per_mw=200e3, max_dollars_per_mw=200e3, itlim=2):
  clusters = {} # Python dictionaries are insertion-ordered, so the clusters will be FIFO as built
  for i in range(napps):
    poc = np.random.choice (poc_list)
    mw = np.random.uniform (min_mw, max_mw)
    costlim = mw * np.random.uniform (min_dollars_per_mw, max_dollars_per_mw)
    app = {'poc':poc, 'mw': mw, 'itlim': itlim, 'costlim': costlim, 'order':i}
    if poc not in clusters:
      clusters[poc] = {'mw': 0.0, 'itlim': 0, 'costlim': 0, 'apps':[]}
    update_poc_cluster (clusters[poc], app)
  queue = []
  for poc, row in clusters.items():
    queue.append ({'poc':poc, 'mw': row['mw'], 'itlim': row['itlim'], 'costlim': row['costlim']})
  return clusters, queue

def print_poc_clusters (clusters):
  print ('APPLICATION CLUSTERS')
  print (' Bus   Req [MW]  MaxCost $M  Itlim  #apps')
  for bus, row in clusters.items():
    napps = len(row['apps'])
    print ('{:4d}   {:8.2f}    {:8.2f} {:5d} {:5d}'.format (bus, row['mw'], row['costlim']/1.0e6, row['itlim'], napps))
    if napps > 1:
      for i in range(napps):
        app = row['apps'][i]
        print ('       {:8.2f}    {:8.2f} {:5d}'.format (app['mw'], app['costlim']/1.0e6, app['itlim']))

def print_queue_results (results):
  print ('CLUSTER STUDY RESULTS')
  print (' Bus   Req [MW]  Add [MW]   HC [MW]   Cost $M   Branch Upgrades')
  for bus, row in results.items():
    brlist = 'None'
    if 'upgrades' in row:
      if row['upgrades'] is not None:
        brlist = str(list(row['upgrades'].keys()))
    print ('{:4d}   {:8.2f}  {:8.2f}  {:8.2f}  {:8.2f}   {:s}'.format (bus, row['req_mw'], row['add_mw'], 
                                                                    row['hc'], row['cost']/1.0e6, brlist))

def print_auction_results (results):
  print ('AUCTION RESULTS')
  print ('Generation by Fuel[GW]')
  print (' '.join(['{:>7s}'.format(x) for x in mpow.FUEL_LIST]))
  fuel_str = ' '.join(['{:7.3f}'.format(results['fuels'][x]) for x in mpow.FUEL_LIST])
  print (fuel_str)

  print (' Bus    HC [MW]')
  for busnum, mw in results['capacity'].items():
    print ('{:4d} {:10.3f}'.format (int(busnum), mw))

  print ('Merit order of upgrades:')
  print (' Br# From   To     muF      MVA      kV  Add MVA    Miles  Cost $M')
  for brnum, row in results['upgrades'].items():
    if row['label'] == 'Line':
      desc = '{:8.2f}'.format (row['miles'])
    else:
      desc = row['label']
    print ('{:4d} {:4d} {:4d} {:7.4f} {:8.2f} {:7.2f} {:8.2f} {:8s} {:8.2f}'.format(brnum, row['fbus'], row['tbus'], row['muF'], 
                                                                                  row['rating'], row['kv'], row['addmva'], 
                                                                                  desc, row['cost']/1.0e6))

def report_branch_limits (r, bus, branch, bLog=False):
  brnum = 0
  scale = 0.0
  cost = 0.0
  # merit order of branch upgrades based on shadow price
  d = {}
  if bLog:
    print ('Branches at limit:')
  for key, val in r['branches'].items():
    muF = val['muF']
    d[key] = muF
    if bLog:
      print ('  {:4d} {:s} {:s}'.format (key, str(val), bes.get_branch_description (branch, bus, key-1, bEstimateCost=True)))
  if len(d) > 0:
    merit = sorted (d.items(), key=lambda x:x[1], reverse=True)
    brnum = merit[0][0]
    scale, cost, miles = bes.get_branch_next_upgrade (branch, bus, brnum-1)
    if bLog:
      print ('Merit Order of Upgrades:', merit)
      print ('Upgrading', brnum, bes.get_branch_description (branch, bus, brnum-1, bEstimateCost=True))
  return brnum, scale, cost

def load_starting_case (base_case):
  # read the exisitng network with valid MVA ratings and generator costs
  mpd = mpow.read_matpower_casefile (base_case, asNumpy=True)

  # verify that mpd is in the form for HCA
  if len(mpd['gencost'][0]) > 6:
    ng = len(mpd['gen'])
    gencost = []
    for i in range(ng):
      gencost.append (mpow.get_hca_gencosts(mpd['genfuel'][i]))
    mpd['gencost'] = np.array (gencost, dtype=float)

  # add the candidate generator for HCA
  mpd['gen'] = np.vstack ((mpd['gen'], 
                          np.array([1.0,0.0,0.0,HCA_QMAX,-HCA_QMAX,1.0,1000.0,0.0,HCA_PMAX,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0])))
  mpd['gentype'].append('DL')
  mpd['genfuel'].append('hca')
  mpd['gencost'] = np.vstack((mpd['gencost'], mpow.get_hca_gencosts('hca')))

  # extra generator data (xgd) including the new one for HCA
  # assume all units have been on for 24 hours to start, so MOST can leave them on or switch them off without restriction
  unit_states = np.ones(len(mpd['gen'])) * 24.0
  mpow.write_xgd_function ('hca_xgd', mpd['gen'], mpd['gencost'], mpd['genfuel'], unit_states, bLog=False)

  G = bes.build_matpower_graph (mpd)
  mpow.write_matpower_casefile (mpd, 'hca_case')
  return mpd, G

def add_renewable (mpd, poc, bes_size, ic_cost, bLog=True, bVerbose=False):
  global bWind
  if bWind:
    genfuel = 'wind'
    gentype = 'WT'
  else:
    genfuel = 'solar'
    gentype = 'PV'
    bWind = True
  qmax = 0.25 * bes_size
  sbase = min(1000.0, bes_size)
  pg = 0.5 * bes_size
  qg = 0.0
  pmin = 0.0
  mpd['gen'] = np.vstack ((mpd['gen'], 
                          np.array([poc,pg,qg,qmax,-qmax,1.0,sbase,0.0,bes_size,pmin,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0])))
  mpd['gentype'].append(gentype)
  mpd['genfuel'].append(genfuel)
  mpd['gencost'] = np.vstack((mpd['gencost'], mpow.get_hca_gencosts(genfuel)))

  unit_states = np.ones(len(mpd['gen'])) * 24.0
  mpow.write_xgd_function ('hca_xgd', mpd['gen'], mpd['gencost'], mpd['genfuel'], unit_states, bLog=bVerbose)

  mpow.write_matpower_casefile (mpd, 'hca_case')
  if bLog:
    print ('  Added {:.2f} MW {:s} at bus {:d} for ${:.3f}M'.format (bes_size, genfuel, poc, ic_cost/1.0e6))
  return mpd

def update_current_case (mpd, brnum, scale):
  idx = brnum-1
  br = mpd['branch']
  br[idx][mpow.BR_R] /= scale
  br[idx][mpow.BR_X] /= scale
  br[idx][mpow.BR_B] *= scale
  br[idx][mpow.RATE_A] *= scale
  br[idx][mpow.RATE_B] *= scale
  br[idx][mpow.RATE_C] *= scale
  G = bes.build_matpower_graph (mpd)
  mpow.write_matpower_casefile (mpd, 'hca_case')
  return mpd, G

def process_renewable_project (poc, mw_size, mpd, G, load_scale, itmax, bLog=False):
  print ('Processing application for {:.2f} MW at bus {:d}'.format (mw_size, poc))
  itcount = 0
  mw_hc = 0.0
  total_cost = 0.0
  upgrades = {}
  while mw_hc < mw_size and itcount < itmax:
    itcount += 1
    cont = bes.rebuild_contingencies (mpd, G, [poc], MIN_SIZE_MVA, MIN_BUS_MVA, MIN_CONT_KV)
    mpow.write_contab_list ('hca_contab', mpd, cont, bLog=False)
    r = hca.bes_hca_fn (sys_name='hca', case_title='hca', load_scale=load_scale, hca_buses=[poc])
    mw_hc = r['buses'][poc]['fuels']['hca']*1000.0
    if mw_hc < mw_size:
      brnum, scale, cost = report_branch_limits (r, mpd['bus'], mpd['branch'])
      if brnum > 0:
        if brnum not in upgrades:
          upgrades[brnum] = 0.0
        upgrades[brnum] += cost
        print ('  HC={:.2f} MW, upgrade branch {:d} by {:.4f} at ${:.3f}M'.format (mw_hc, brnum, scale, cost/1.0e6))
        mpd, G = update_current_case (mpd, brnum, scale)
        total_cost += cost

  return mpd, G, total_cost, mw_hc, upgrades

def rollback_grid_upgrades (mpd, pre_project_branches, bLog=False):
  mpd['branch'] = np.copy (pre_project_branches)
  G = bes.build_matpower_graph (mpd)
  mpow.write_matpower_casefile (mpd, 'hca_case')
  return mpd, G

def process_auction (poc_buses, sys_config, bLog=True):
  base_case, load_scale = configure_queue (sys_config)
  print ('***********************************************')
  print ('Auction Process on {:s}, POC buses={:s}'.format (base_case, str(poc_buses)))
  mpd = mpow.read_matpower_casefile (base_case, asNumpy=True)

  # verify that mpd is in the form for HCA
  if len(mpd['gencost'][0]) > 6:
    if bLog:
      print ('Fixing generator costs')
    ng = len(mpd['gen'])
    gencost = []
    for i in range(ng):
      gencost.append (mpow.get_hca_gencosts(mpd['genfuel'][i]))
    mpd['gencost'] = np.array (gencost, dtype=float)

  # add the candidate generators at each poc bus
  for bus in poc_buses:
    mpd['gen'] = np.vstack ((mpd['gen'], 
                             np.array([bus,0.0,0.0,HCA_QMAX,-HCA_QMAX,1.0,1000.0,0.0,HCA_PMAX,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0])))
    mpd['gentype'].append('DL')
    mpd['genfuel'].append('hca')
    mpd['gencost'] = np.vstack((mpd['gencost'], mpow.get_hca_gencosts('hca')))

  # extra generator data (xgd) including the new one for HCA
  # assume all units have been on for 24 hours to start, so MOST can leave them on or switch them off without restriction
  unit_states = np.ones(len(mpd['gen'])) * 24.0
  mpow.write_xgd_function ('hca_xgd', mpd['gen'], mpd['gencost'], mpd['genfuel'], unit_states, bLog=bLog)

  G = bes.build_matpower_graph (mpd)
  mpow.write_matpower_casefile (mpd, 'hca_case')

  cont = bes.rebuild_contingencies (mpd, G, poc_buses, MIN_SIZE_MVA, MIN_BUS_MVA, MIN_CONT_KV, bAuction=True)
  mpow.write_contab_list ('hca_contab', mpd, cont, bLog=False)

  if bLog:
    print ('Generation by Fuel[GW]')
    print (' '.join(['{:>7s}'.format(x) for x in mpow.FUEL_LIST]))
  fscript, fsummary = mpow.write_hca_solve_file ('hca', load_scale=load_scale, quiet=not bLog)

  if os.path.exists(fsummary):
    os.remove(fsummary)

  mpow.run_matpower_and_wait (fscript, quiet=not bLog)

  if not os.path.exists(fsummary):
    print ('** Auction HCA solution failed **')
    return

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

  results = {'capacity':{}, 'upgrades':{}, 'fuels':{}}
  # summarize the generation by fuel type
  fuel_Pg = {}
  for fuel in mpow.FUEL_LIST:
    fuel_Pg[fuel] = 0.0
  for i in range(ng):
    fuel = mpd['genfuel'][i]
    fuel_Pg[fuel] += meanPgen[i]
  for fuel in mpow.FUEL_LIST:
    fuel_Pg[fuel] *= 0.001
  results['fuels'] = fuel_Pg
  if bLog:
    fuel_str = ' '.join(['{:7.3f}'.format(fuel_Pg[x]) for x in mpow.FUEL_LIST])
    print (fuel_str)

  if bLog:
    print (' Bus    HC [MW]')
  for i in range (len(mpd['genfuel'])):
    if mpd['genfuel'][i] == 'hca':
      mw = meanPg[i]
      bus = mpd['gen'][i][mpow.GEN_BUS]
      results['capacity'][bus] = mw
      if bLog:
        print ('{:4d} {:10.3f}'.format (int(bus), mw))

  if bLog:
    print ('Merit order of upgrades:')
    print (' Br# From   To     muF      MVA      kV  Add MVA    Miles  Cost $M')
  r = {}
  for i in range(nl):
    if meanmuF[i] > 0.0:
      r[i+1] = meanmuF[i]
  merit = sorted (r.items(), key=lambda x:x[1], reverse=True)
  for pair in merit:
    i = pair[0]
    muF = pair[1]
    rating = mpd['branch'][i-1][mpow.RATE_A]
    fbus = int(mpd['branch'][i-1][mpow.F_BUS])
    tbus = int(mpd['branch'][i-1][mpow.T_BUS])
    kv = max (mpd['bus'][fbus-1][mpow.BASE_KV], mpd['bus'][tbus-1][mpow.BASE_KV])
    tap = mpd['branch'][i-1][mpow.TAP]
    scale, cost, miles = bes.get_branch_next_upgrade (mpd['branch'], mpd['bus'], i-1)
    if tap > 0.0:
      label = 'Xfmr'
    elif miles < 0.0:
      label = 'Scap'
    else:
      label = 'Line'
    addmva = rating * (scale - 1.0)
    results['upgrades'][i] = {'fbus':fbus, 'tbus':tbus, 'muF':muF, 'rating':rating, 'kv': kv, 'addmva': addmva, 'label': label, 'miles': miles, 'cost': cost}
    if bLog:
      if label == 'Line':
        label = '{:8.2f}'.format (miles)
      print ('{:4d} {:4d} {:4d} {:7.4f} {:8.2f} {:7.2f} {:8.2f} {:8s} {:8.2f}'.format(i, fbus, tbus, muF, rating, kv, addmva, label, cost/1.0e6))
  return results

def print_system_generators (mpd, idx):
  print ('System generation before application {:d}'.format (idx))
  print ('Nbr Bus       MW Type Fuel')
  ng = len(mpd['gen'])
  for i in range(ng):
    print ('{:3d} {:3d} {:8.2f} {:4s} {:8s}'.format (i+1, int(mpd['gen'][i][mpow.GEN_BUS]), mpd['gen'][i][mpow.PMAX], mpd['gentype'][i], mpd['genfuel'][i]))

def process_queue (queue, sys_config, bLog=True, bVerbose=False):
  base_case, load_scale = configure_queue (sys_config)
  print ('***********************************************')
  print ('Queue Process on {:d} bus application cluster(s) for {:s}'.format (len(queue), base_case))
  mpd, G = load_starting_case(base_case)

  results = {}
  idx = 0
  for app in queue:
    results[app['poc']] = {'hc':0.0, 'req_mw':app['mw'], 'add_mw':0.0, 'cost':0.0, 'upgrades':None}
    idx += 1
    if bVerbose:
      print_system_generators (mpd, idx)
    pre_project_branches = np.copy (mpd['branch']) # in case we have to roll back upgrades on projects that don't move forward
    mpd, G, cost, hc, upgrades = process_renewable_project (app['poc'], app['mw'], mpd, G, load_scale, app['itlim'], bLog=bLog)
    results[app['poc']]['cost'] = cost
    if cost > 0.0:
      results[app['poc']]['upgrades'] = upgrades
    results[app['poc']]['hc'] = hc
    if hc >= app['mw']:
      if cost <= app['costlim']:
        results[app['poc']]['add_mw'] = app['mw']
        if cost > 0.0:
          results[app['poc']]['upgrades'] = upgrades
        mpd = add_renewable (mpd, app['poc'], app['mw'], cost, bLog=True)
      else:
        if bLog:
          print ('  IX Cost ${:.3f}M is too high, HC={:.3f} MW'.format (cost/1.0e6, hc))
        if cost > 0.0:
          mpd, G = rollback_grid_upgrades (mpd, pre_project_branches, bLog=bLog)
    else:
      if bLog:
        print ('  HC {:.3f} MW is too low'.format (hc))
      if cost > 0.0:
        mpd, G = rollback_grid_upgrades (mpd, pre_project_branches, bLog=bLog)
  return (results)


