# Copyright (C) 2023 Battelle Memorial Institute
# file: bq_simulations.py
"""Simulate a sequence of system impact studies or hosting-capacity auction.
"""
import sys
import time
import json
import numpy as np
import i2x.bes_queue as bq

# partial copy from bes_cases.py; _wmva.m should already be built
SYSTEMS = [
  {'name': 'IEEE118', 'load_scale':0.6748, 'min_size_contingency_mva': 400.0,  'prep_file': 'IEEE118_prep.json'},
  {'name': 'WECC240', 'load_scale':1.0425, 'min_size_contingency_mva': 5000.0, 'prep_file': 'WECC240_prep.json'},
  {'name': 'IEEE39', 'load_scale':1.0000,  'min_size_contingency_mva': 1000.0, 'prep_file': 'IEEE39_prep.json'}
]

CASES = [ 
  # for IEEE 39-bus; fixed POC definitions are the same for auction and clusters
  {'pocs':[14], 'napps':1, 'min_mw': 500.0, 'max_mw':500.0, 'min_cost': 0.2e6, 'max_cost': 0.2e6},
  {'pocs':[15], 'napps':1, 'min_mw': 500.0, 'max_mw':500.0, 'min_cost': 0.2e6, 'max_cost': 0.2e6},
  {'pocs':[10, 11, 12, 13, 14, 15], 'napps':3, 'min_mw': 500.0, 'max_mw':500.0, 'min_cost': 0.2e6, 'max_cost': 0.2e6},
  # for IEEE 118-bus; random number of auction and cluster POCs, which are the same
  {'nauc_pocs':5, 'napps':10, 'min_mw': 150.0, 'max_mw':400.0, 'min_cost': 0.1e6, 'max_cost': 0.3e6},
  # for WECC 240-bus; random number of auction and cluster POCs, which are the same
  {'nauc_pocs':5, 'napps':10, 'min_mw': 200.0, 'max_mw':1000.0, 'min_cost': 0.1e6, 'max_cost': 0.3e6}
]

if __name__ == '__main__':
  sys_id = 2
  case_id = 0
  if len(sys.argv) > 1:
    sys_id = int(sys.argv[1])
    if len(sys.argv) > 2:
      case_id = int(sys.argv[2])

  row = SYSTEMS[sys_id]
  lp = open (row['prep_file']).read()
  all_pocs = json.loads(lp)['hca_buses']
  sys_config = {
    'base_case': row['name'] + '_wmva.m',
    'load_scale': row['load_scale'],
    'MIN_SIZE_MVA': row['min_size_contingency_mva']
  }

  row = CASES[case_id]
  if 'pocs' in row:
    auction_buses = row['pocs']
    cluster_buses = auction_buses
  elif 'nauc_pocs' in row:
    auction_buses = np.random.choice (all_pocs, size=row['nauc_pocs'], replace=False)
    cluster_buses = auction_buses
    print ('Auction Bus List', auction_buses)
  else:
    print ('===> either "pocs" or "nauc_pocs" must be defined for case {:d}'.format (case_id))
    quit()
  napps = row['napps']
  min_mw = row['min_mw']
  max_mw = row['max_mw']
  min_cost = row['min_cost']
  max_cost = row['max_cost']

  start = time.time ()
  print ('System {:s}, Req MW=[{:.2f},{:.2f}], Max $M/MW=[{:.2f},{:.2f}], Nauc={:d}, Ncls={:d}, Napp={:d}'.format (sys_config['base_case'],
                                                                                                        min_mw, max_mw, min_cost/1.0e6,
                                                                                                        max_cost/1.0e6, len(auction_buses),
                                                                                                        len(cluster_buses), napps))
  results = bq.process_auction (poc_buses=auction_buses, sys_config=sys_config, bLog=False)
  bq.print_auction_results (results)

  clusters, queue = bq.form_clusters (napps=napps, poc_list=cluster_buses, min_mw=min_mw, max_mw=max_mw, 
                                      min_dollars_per_mw=min_cost, max_dollars_per_mw=max_cost)
  results = bq.process_queue (queue=queue, sys_config=sys_config, bLog=False)

  bq.print_poc_clusters (clusters)
  bq.print_queue_results (results)

  print ('{:.2f} seconds elapsed'.format(time.time() - start))

