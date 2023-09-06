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
  {'tag':'3sag', 'type':'abcg', 'L':LFWEAK},
  {'tag':'3pg', 'type':'abcg', 'L':0.0001},
  {'tag':'1pg', 'type':'ag', 'L':0.0001},
  {'tag':'2pg', 'type':'bcg', 'L':0.0001},
  {'tag':'2p', 'type':'bc', 'L':0.0001}
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

qvals = [
  {'tag': 'q0', 'value': 0.0},
  {'tag': 'qp', 'value': 0.3287*ICR},
  {'tag': 'qn', 'value': -0.3287*ICR}
]

fvals = [
  {'tag': 'of', 'value': 61.8},
  {'tag': 'uf', 'value': 57.0}
]

avals = [
  {'tag': 'an', 'value': -25.0},
  {'tag': 'ap', 'value': 25.0}
]

stepvals = [
  {'tag':'stvref', 'mode':'POC_VOLTAGE', 'tmax':50.0, 
      'V1':1.05, 'V2':0.95, 'P1':ICR, 'P2':ICR, 'Q1':0.0, 'Q2':0.0, 'PF1':1.0, 'PF2':1.0},
  {'tag':'stqref', 'mode':'FIXED_Q', 'tmax':50.0, 
      'V1':1.0, 'V2':1.0, 'P1':ICR, 'P2':ICR, 'Q1':0.3287*ICR, 'Q2':-0.3287*ICR, 'PF1':1.0, 'PF2':1.0},
  {'tag':'stpfref', 'mode':'POWER_FACTOR', 'tmax':50.0, 
      'V1':1.0, 'V2':1.0, 'P1':ICR, 'P2':ICR, 'Q1':0.0, 'Q2':0.0, 'PF1':0.95, 'PF2':-0.95},
  {'tag':'stpref', 'mode':'POC_VOLTAGE', 'tmax':40.0, 
      'V1':1.0, 'V2':1.0, 'P1':0.5*ICR, 'P2':0.04*ICR, 'Q1':0.0, 'Q2':0.0, 'PF1':1.0, 'PF2':1.0}
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

def set_fault_type (fcomp, ftype):
  A=False
  B=False
  C=False
  G=False
  if 'a' in ftype:
    A=True
  if 'b' in ftype:
    B=True
  if 'c' in ftype:
    C=True
  if 'g' in ftype:
    G=True
  fcomp.parameters (A=A, B=B, C=C, G=G)

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

def run_uvrt_tests (prj, d):
  start = time.time()
  print ('Running undervoltage ridethrough tests:')
  prj.parameters (time_duration=10.0)
  d['Grid'].parameters (Z1=Z1WEAK)
  d['FaultT'].parameters (TF=5.0)
  d['FaultT'].parameters (DF=0.16)
  set_flat_control (d['PhsrcTable'], 0.0)
  set_flat_control (d['kVsrcTable'], KV)
  set_flat_control (d['FsrcTable'], FREQ)
  set_flat_control (d['VrefTable'], 1.0)
  set_flat_control (d['PrefTable'], ICR)
  d['Solar_Lib:Simple_PPC'].parameters (con_mode='FIXED_Q')
  for qval in qvals:
    set_flat_control (d['QrefTable'], qval['value'])
    for flt in faults:
      d['FaultL'].parameters (L=flt['L'])
      set_fault_type (d['Fault'], flt['type'])
      tag = 'uv{:s}{:s}'.format (qval['tag'], flt['tag'])
      if len(tag) > 8:
        print ('** "{:s}" should be no more than 8 characters'.format (tag))
      d['Recorder'].parameters (FName=tag)
      print ('  simulating case {:s}'.format (tag))
      prj.run()
  print ('  finished: {:.2f} seconds elapsed'.format(time.time() - start))

def run_ovrt_tests (prj, d):
  start = time.time()
  print ('Running overvoltage ridethrough tests:')
  prj.parameters (time_duration=20.0)
  d['Grid'].parameters (Z1=Z1WEAK)
  d['FaultT'].parameters (TF=999.0)
  set_flat_control (d['PhsrcTable'], 0.0)
  set_flat_control (d['FsrcTable'], FREQ)
  set_flat_control (d['VrefTable'], 1.0)
  set_flat_control (d['PrefTable'], ICR)
  d['Solar_Lib:Simple_PPC'].parameters (con_mode='FIXED_Q')
  d['kVsrcTable'].parameters(N=6, 
                             X1=0.000, Y1=KV,
                             X2=5.000, Y2=KV,
                             X3=5.001, Y3=1.2*KV,
                             X4=6.000, Y4=1.2*KV,
                             X5=6.001, Y5=KV,
                             X6=999.0, Y6=KV)
  for qval in qvals:
    set_flat_control (d['QrefTable'], qval['value'])
    tag = 'ov{:s}'.format (qval['tag'])
    if len(tag) > 8:
      print ('** "{:s}" should be no more than 8 characters'.format (tag))
    d['Recorder'].parameters (FName=tag)
    print ('  simulating case {:s}'.format (tag))
    prj.run()
  print ('  finished: {:.2f} seconds elapsed'.format(time.time() - start))

def run_freq_tests (prj, d):
  start = time.time()
  print ('Running frequency ridethrough tests:')
  prj.parameters (time_duration=40.0)
  d['Grid'].parameters (Z1=Z1WEAK)
  d['FaultT'].parameters (TF=999.0)
  set_flat_control (d['PhsrcTable'], 0.0)
  set_flat_control (d['kVsrcTable'], KV)
  set_flat_control (d['VrefTable'], 1.0)
  set_flat_control (d['QrefTable'], 0.0)
  d['Solar_Lib:Simple_PPC'].parameters (con_mode='FIXED_Q')
  for pval in pvals:
    set_flat_control (d['PrefTable'], pval['value'])
    for fval in fvals:
      d['FsrcTable'].parameters(N=6, 
                                X1= 0.000, Y1=60.0,
                                X2= 5.000, Y2=60.0,
                                X3= 5.010, Y3=fval['value'],
                                X4=25.000, Y4=fval['value'],
                                X5=25.010, Y5=60.0,
                                X6=999.0,  Y6=60.0)
      tag = '{:s}{:s}'.format (fval['tag'], pval['tag'])
      if len(tag) > 8:
        print ('** "{:s}" should be no more than 8 characters'.format (tag))
      d['Recorder'].parameters (FName=tag)
      print ('  simulating case {:s}'.format (tag))
      prj.run()
  print ('  finished: {:.2f} seconds elapsed'.format(time.time() - start))

def run_angle_tests (prj, d):
  start = time.time()
  print ('Running angle ridethrough tests:')
  prj.parameters (time_duration=40.0)
  d['Grid'].parameters (Z1=Z1WEAK)
  d['FaultT'].parameters (TF=999.0)
  set_flat_control (d['FsrcTable'], 60.0)
  set_flat_control (d['kVsrcTable'], KV)
  set_flat_control (d['VrefTable'], 1.0)
  set_flat_control (d['QrefTable'], 0.0)
  d['Solar_Lib:Simple_PPC'].parameters (con_mode='FIXED_Q')
  for pval in pvals:
    set_flat_control (d['PrefTable'], pval['value'])
    for aval in avals:
      d['PhsrcTable'].parameters(N=6, 
                                X1= 0.000, Y1=0.0,
                                X2= 5.000, Y2=0.0,
                                X3= 5.010, Y3=aval['value'],
                                X4=25.000, Y4=aval['value'],
                                X5=25.010, Y5=0.0,
                                X6=999.0,  Y6=0.0)
      tag = '{:s}{:s}'.format (aval['tag'], pval['tag'])
      if len(tag) > 8:
        print ('** "{:s}" should be no more than 8 characters'.format (tag))
      d['Recorder'].parameters (FName=tag)
      print ('  simulating case {:s}'.format (tag))
      prj.run()
  print ('  finished: {:.2f} seconds elapsed'.format(time.time() - start))

def run_step_tests (prj, d):
  start = time.time()
  print ('Running control reference step tests:')
  d['Grid'].parameters (Z1=Z1WEAK)
  d['FaultT'].parameters (TF=999.0)
  set_flat_control (d['FsrcTable'], 60.0)
  set_flat_control (d['kVsrcTable'], KV)
  set_flat_control (d['PhsrcTable'], 0.0)
  d['Solar_Lib:Simple_PPC'].parameters (con_mode='FIXED_Q')
  for step in stepvals:
    prj.parameters (time_duration=step['tmax'])
    d['Solar_Lib:Simple_PPC'].parameters (con_mode=step['mode'])
    d['PrefTable'].parameters(N=8, 
                              X1= 0.000, Y1=ICR,
                              X2= 5.000, Y2=ICR,
                              X3= 5.010, Y3=step['P1'],
                              X4=15.000, Y4=step['P1'],
                              X5=15.010, Y5=step['P2'],
                              X6=25.000, Y6=step['P2'],
                              X7=25.010, Y7=ICR,
                              X8=999.0,  Y8=ICR)
    d['VrefTable'].parameters(N=10, 
                              X1= 0.000, Y1=1.0,
                              X2= 5.000, Y2=1.0,
                              X3= 5.010, Y3=step['V1'],
                              X4=15.000, Y4=step['V1'],
                              X5=15.010, Y5=1.0,
                              X6=25.000, Y6=1.0,
                              X7=25.010, Y7=step['V2'],
                              X8=35.000, Y8=step['V2'],
                              X9=35.010, Y9=1.0,
                              X10=999.0, Y10=1.0)
    d['QrefTable'].parameters(N=10, 
                              X1= 0.000, Y1=0.0,
                              X2= 5.000, Y2=0.0,
                              X3= 5.010, Y3=step['Q1'],
                              X4=15.000, Y4=step['Q1'],
                              X5=15.010, Y5=0.0,
                              X6=25.000, Y6=0.0,
                              X7=25.010, Y7=step['Q2'],
                              X8=35.000, Y8=step['Q2'],
                              X9=35.010, Y9=0.0,
                              X10=999.0, Y10=0.0)
    d['PFrefTable'].parameters(N=10, 
                              X1= 0.000, Y1=1.0,
                              X2= 5.000, Y2=1.0,
                              X3= 5.010, Y3=step['PF1'],
                              X4=15.000, Y4=step['PF1'],
                              X5=15.010, Y5=1.0,
                              X6=25.000, Y6=1.0,
                              X7=25.010, Y7=step['PF2'],
                              X8=35.000, Y8=step['PF2'],
                              X9=35.010, Y9=1.0,
                              X10=999.0, Y10=1.0)
    tag = step['tag']
    if len(tag) > 8:
      print ('** "{:s}" should be no more than 8 characters'.format (tag))
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
#  run_flatstart_tests (prj, d)
#  run_uvrt_tests (prj, d)
#  run_ovrt_tests (prj, d)
#  run_freq_tests (prj, d)
#  run_angle_tests (prj, d)
  run_step_tests (prj, d)


