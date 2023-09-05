# Copyright (C) 2023 Battelle Memorial Institute
# file: PlantScript.py
""" Automating plant tests in PSCAD for the EMT bootcamp.

Preconditions:
1) PSCAD has been launched
2) Solar5 project has been loaded into PSCAD
3) Components to be modified have been assigned unique names
"""

import mhi.pscad
import time

# plant/grid parameters in MW, kV, Hz
ICR = 100.0
PMIN = 0.0
KV = 230.0
FREQ = 60.0
Z1WEAK = 148.1
LFWEAK = Z1WEAK / 377.0

cmp_names = [
  'Fault', 
  'FaultL', 
  'FaultT', 
  'Recorder', 
  'Grid', 
  'Solar_Lib:Simple_PPC',
  'Solar_Lib:VSC_AVM', 
  'VrefTable', 
  'QrefTable', 
  'PrefTable', 
  'PFrefTable',
  'kVsrcTable', 
  'FsrcTable', 
  'PhsrcTable'
]

faults = [
  {'tag':'abcg50', 'L':0.0264, 'Lweak': LFWEAK},
  {'tag':'abcg01', 'L':0.0001},
  {'tag':'ag01', 'L':0.0001},
  {'tag':'bcg01', 'L':0.0001},
  {'tag':'bc01', 'L':0.0001}
]

modes = [
  {'tag': 'ctlV', 'value': 'POC_VOLTAGE'},
  {'tag': 'ctlPF', 'value': 'POWER_FACTOR'}, 
  {'tag': 'ctlQ', 'value': 'FIXED_Q'}
]

pvals = [
  {'tag': 'icr', 'value': ICR},
  {'tag': 'min', 'value': PMIN}
]

flats = [
  {'tag': 'v', 'mode': 'POC_VOLTAGE', 'qval': 0.0, 'pfval': 1.0},
  {'tag': 'q0', 'mode': 'FIXED_Q', 'qval': 0.0, 'pfval': 1.0},
  {'tag': 'qp', 'mode': 'FIXED_Q', 'qval': 0.3287*ICR, 'pfval': 1.0},
  {'tag': 'qn', 'mode': 'FIXED_Q', 'qval': -0.3287*ICR, 'pfval': 1.0},
  {'tag': 'pf0', 'mode': 'POWER_FACTOR', 'qval': 0.0, 'pfval': 1.0},
  {'tag': 'pfp', 'mode': 'POWER_FACTOR', 'qval': 0.0, 'pfval': 0.95},
  {'tag': 'pfn', 'mode': 'POWER_FACTOR', 'qval': 0.0, 'pfval': -0.95}
]

def set_flat_control (table, val):
  table.parameters(N=2, X1=0.0, X2=999.0, Y1=val, Y2=val)

def run_flatstart_tests (prj, d):
  # run the model initialization tests, nominal source, no fault, weak grid
  start = time.time()
  print ('Running model flat-start tests:')
  prj.parameters (time_duration=20.0)
  d['Grid'].parameters (Z1=Z1WEAK)
  d['FaultT'].parameters (TF=999.9)
  set_flat_control (d['PhsrcTable'], 0.0)
  set_flat_control (d['kVsrcTable'], KV)
  set_flat_control (d['FsrcTable'], FREQ)
  set_flat_control (d['VrefTable'], 1.0)
  # run 7 flat starts for each power level
  for pval in pvals:
    set_flat_control (d['PrefTable'], pval['value'])
    for flat in flats:
      tag = 'fs{:s}{:s}'.format (pval['tag'], flat['tag'])
      if len(tag) > 8:
        print ('** "{:s}" should be no more than 8 characters'.format (tag))
      set_flat_control (d['QrefTable'], flat['qval'])
      set_flat_control (d['PFrefTable'], flat['pfval'])
      d['Solar_Lib:Simple_PPC'].parameters (con_mode=flat['mode'])
      d['Recorder'].parameters (FName=tag)
      print ('  simulating case {:s}'.format (tag))
      prj.run()
  print ('  finished: {:.2f} seconds elapsed'.format(time.time() - start))

def load_interfaces (prj_name, bListParameters = False):
  try:
    pscad = mhi.pscad.application()
  except:
    print ('** could not find or launch PSCAD')
    quit()
  try:
    prj = pscad.project (prj_name)
  except:
    print ('** did not find project "{:s}" (exception)'.format(prj_name))
    quit()
  if prj is None:
    print ('** did not find project "{:s}" (returns None)'.format(prj_name))
    quit()
  d = {}
  bFailed = False
  # interfaces to components that will be modified
  for c in cmp_names:
    d[c] = prj.find_first(c)
    if d[c] is None:
      print ('*** named component "{:s}" is missing'.format (c))
      bFailed = True
    elif bListParameters:
      print ('"{:s}" parameters: '.format (c), d[c].parameters())
  if bFailed:
    quit()
  return prj, d

if __name__ == '__main__':
  prj, d = load_interfaces ('Solar5')
  run_flatstart_tests (prj, d)

  # table-driven parametric study
# for row in cases:
#   faultL.parameters (L=row['L'])
#   recorder.parameters (FName=row['tag'])
#   A=False
#   B=False
#   C=False
#   G=False
#   if 'a' in row['tag']:
#     A=True
#   if 'b' in row['tag']:
#     B=True
#   if 'c' in row['tag']:
#     C=True
#   if 'g' in row['tag']:
#     G=True
#   fault.parameters (A=A, B=B, C=C, G=G)
#   prj.run()

