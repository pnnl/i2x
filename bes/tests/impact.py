# Copyright (C) 2023 Battelle Memorial Institute
# file: impact.py
"""Simulate a sequence of system impact studies.
"""
import numpy as np
import i2x.bes_hca as hca
import i2x.bes_upgrades as bes
import i2x.mpow_utilities as mpow

bes_size = 5000.0
bes_buses = [6, 3, 8]
HCA_PMAX = 30000.0
HCA_QMAX = 10000.0

bWind = False # alternate addition of wind and solar projects

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
    scale, cost = bes.get_branch_next_upgrade (branch, bus, brnum-1)
    if bLog:
      print ('Merit Order of Upgrades:', merit)
      print ('Upgrading', brnum, bes.get_branch_description (branch, bus, brnum-1, bEstimateCost=True))
  return brnum, scale, cost

def load_starting_case ():
  # read the exisitng network with valid MVA ratings and generator costs
  mpd = mpow.read_matpower_casefile ('hca_wmva.m', asNumpy=True)

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

def add_renewable (poc, bes_size, ic_cost):
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
  mpow.write_xgd_function ('hca_xgd', mpd['gen'], mpd['gencost'], mpd['genfuel'], unit_states, bLog=False)

  mpow.write_matpower_casefile (mpd, 'hca_case')
  print ('  Added {:.2f} MW {:s} at bus {:d} for ${:.3f}M'.format (bes_size, genfuel, poc, cost/1.0e6))
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

def process_renewable_project (poc, mw_size, mpd, G, load_scale=2.75, itmax=3):
  print ('Processing application for {:.2f} MW at bus {:d}'.format (mw_size, poc))
  itcount = 0
  mw_hc = 0.0
  total_cost = 0.0
  while mw_hc < mw_size and itcount < itmax:
    itcount += 1
    cont = bes.rebuild_contingencies (mpd, G, poc)
    mpow.write_contab_list ('hca_contab', mpd, cont, bLog=False)
    r = hca.bes_hca_fn (sys_name='hca', case_title='hca', load_scale=load_scale, hca_buses=[poc])
    mw_hc = r['buses'][poc]['fuels']['hca']*1000.0
    if mw_hc < mw_size:
      brnum, scale, cost = report_branch_limits (r, mpd['bus'], mpd['branch'])
      if brnum > 0:
        print ('  HC={:.2f} MW, upgrade branch {:d} by {:.4f} at ${:.3f}M'.format (mw_hc, brnum, scale, cost/1.0e6))
        mpd, G = update_current_case (mpd, brnum, scale)
        total_cost += cost

  return mpd, G, total_cost, mw_hc

def rollback_grid_upgrades (mpd, pre_project_branches):
  mpd['branch'] = np.copy (pre_project_branches)
  G = bes.build_matpower_graph (mpd)
  mpow.write_matpower_casefile (mpd, 'hca_case')
  return mpd, G

if __name__ == '__main__':
  queue = [{'poc':6, 'mw': 5000.0, 'itlim': 3, 'costlim': 1000.0e6},
           {'poc':3, 'mw': 4400.0, 'itlim': 3, 'costlim':  500.0e6},
           {'poc':8, 'mw': 2000.0, 'itlim': 3, 'costlim': 1300.0e6}
          ]
  mpd, G = load_starting_case()

  for app in queue:
    pre_project_branches = np.copy (mpd['branch']) # in case we have to roll back upgrades on projects that don't move forward
    mpd, G, cost, hc = process_renewable_project (app['poc'], app['mw'], mpd, G)
    if hc >= app['mw']:
      if cost <= app['costlim']:
        mpd = add_renewable (app['poc'], app['mw'], cost)
      else:
        print ('  IX Cost ${:.3f}M is too high, HC={:.3f} MW'.format (cost/1.0e6, hc))
        if cost > 0.0:
          mpd, G = rollback_grid_upgrades (mpd, pre_project_branches)
    else:
      print ('  HC {:.3f} MW is too low'.format (hc))
      if cost > 0.0:
        mpd, G = rollback_grid_upgrades (mpd, pre_project_branches)

