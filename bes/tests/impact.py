# Copyright (C) 2023 Battelle Memorial Institute
# file: impact.py
"""Simulate a sequence of system impact studies.
"""
import os
import numpy as np
import i2x.bes_queue as bq

if __name__ == '__main__':
  sys_config = {
    'base_case': 'hca_wmva.m',
    'load_scale': 2.75
  }
  poc_buses=[6, 3, 8]

  bq.process_auction (poc_buses=poc_buses, sys_config=sys_config)

  queue = [{'poc':6, 'mw': 5000.0, 'itlim': 3, 'costlim': 1000.0e6},
           {'poc':3, 'mw': 4400.0, 'itlim': 3, 'costlim':  500.0e6},
           {'poc':8, 'mw': 2000.0, 'itlim': 3, 'costlim': 1300.0e6}
          ]
  bq.process_queue (queue=queue, sys_config=sys_config)

