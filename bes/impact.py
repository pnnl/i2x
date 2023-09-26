# Copyright (C) 2023 Battelle Memorial Institute
# file: impact.py
"""Simulate a sequence of system impact studies or hosting-capacity auction.
"""
import sys
import time
import i2x.bes_queue as bq
from bes_cases import *
import numpy as np

if __name__ == '__main__':
  case_id = 2
  if len(sys.argv) > 1:
    case_id = int(sys.argv[1])
  sys_config = {
    'base_case': CASES[case_id]['name'] + '_wmva.m',
    'load_scale': CASES[case_id]['load_scale'],
    'MIN_SIZE_MVA': CASES[case_id]['min_contingency_mva']
  }
  #poc_buses=[14]
  poc_buses=[10, 11, 12, 13, 14, 15]

  start = time.time ()
  results = bq.process_auction (poc_buses=poc_buses, sys_config=sys_config, bLog=False)
  bq.print_auction_results (results)

  clusters, queue = bq.form_clusters (napps=3, poc_list=[15], min_mw=500.0, max_mw=500.0, 
                                      min_dollars_per_mw=0.2e6, max_dollars_per_mw=0.2e6)
  results = bq.process_queue (queue=queue, sys_config=sys_config, bLog=True)

  bq.print_poc_clusters (clusters)
  bq.print_queue_results (results)

  print ('{:.2f} seconds elapsed'.format(time.time() - start))

