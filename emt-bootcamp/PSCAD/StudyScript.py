# Copyright (C) 2023 Battelle Memorial Institute
# file: StudyScript.py
""" Automating system study cases in PSCAD for the EMT bootcamp.

Preconditions:
1) PSCAD has been launched
2) SolarSystem project has been loaded into PSCAD
3) Components to be modified have been assigned unique names
"""

import mhi.pscad
import time

cmp_names = [
  'Recorder'
]

line_sets = [
  {'tag':'L15', 'fault':'FaultTime1', 'local_breaker':'Brk2Time', 'remote_breaker':'Brk1Time'},
  {'tag':'L4',  'fault':'FaultTime2', 'local_breaker':'Brk4Time', 'remote_breaker':'Brk3Time'},
  {'tag':'L13', 'fault':'FaultTime3', 'local_breaker':'Brk6Time', 'remote_breaker':'Brk5Time'}
]

# the set of breakers and line fault can be in one of three states to start a simulation:
# 1) bLineOut = True ==> both breakers start open and never close, fault is never applied during simulation
# 2) bFault = True ==> both breakers start closed and open at 5.035s, fault on at 5.0s
# 3) bLineOut & bFault = False ==> both breakers start close and never open, fault is never applied during simulation
def set_line_state (d, pair, bLineOut=False, bFault=False):
  cfault = d[pair['fault']]
  clocal = d[pair['local_breaker']]
  cremote = d[pair['remote_breaker']]
  if bLineOut:
    cfault.parameters(TF=95.0)
    clocal.parameters(INIT='OPEN', TO1=95.0)
    cremote.parameters(INIT='OPEN', TO1=95.0)
  elif bFault:
    cfault.parameters(TF=5.0)
    clocal.parameters(INIT='CLOSE', TO1=5.035)
    cremote.parameters(INIT='CLOSE', TO1=5.035)
  else:
    cfault.parameters(TF=95.0)
    clocal.parameters(INIT='CLOSE', TO1=95.0)
    cremote.parameters(INIT='CLOSE', TO1=95.0)

def set_recorder (d, root):
  if len(root) > 8:
    print ('** "{:s}" should be no more than 8 characters'.format (root))
  d['Recorder'].parameters (FName=root)

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
  for pair in line_sets:
    c = pair['fault']
    d[c] = prj.find_first(c)
    if d[c] is None:
      print ('*** Fault time component "{:s}" is missing for line set {:s}'.format (c, pair['tag']))
      bFailed = True
    elif bListParameters:
      print ('"{:s}" parameters: '.format (c), d[c].parameters())
    for end in ['local_breaker', 'remote_breaker']:
      c = pair[end]
      d[c] = prj.find_first(c)
      if d[c] is None:
        print ('*** {:s} time component "{:s}" is missing for line set {:s}'.format (end, c, pair['tag']))
        bFailed = True
      elif bListParameters:
        print ('"{:s}" parameters: '.format (c), d[c].parameters())
  if bFailed:
    quit()
  return prj, d

if __name__ == '__main__':
  start = time.time()
  print ('Running system fault cases with N-1 contingencies:')

  prj, d = load_interfaces ('SolarSystem', bListParameters=False)
  prj.parameters (time_duration=10.0)
  for case in line_sets:
    # build the list of other lines connected to the bus of interest
    others = []
    for val in line_sets:
      if val['tag'] != case['tag']:
        others.append (val)
    # N-0 case
    print ('**********************')
    root = '{:s}_x0'.format (case['tag'])
    set_recorder (d, root)
    set_line_state (d, case, bLineOut=False, bFault=True)
    for val in others:
      set_line_state (d, val, bLineOut=False, bFault=False)
    print ('N-0 fault on line to {:s}, filename {:s}'.format (case['tag'], root))
    prj.run()

    # N-1 cases
    for val in others:
      root = '{:s}_x{:s}'.format (case['tag'], val['tag'])
      set_recorder (d, root)
      # this parallel line is out of service
      set_line_state (d, val, bLineOut=True, bFault=False)
      # other parallel lines back in service, except the line to be faulted
      for val2 in others:
        if val2['tag'] != val['tag']:
          if val2['tag'] != case['tag']:
            set_line_state (d, val2, bLineOut=False, bFault=False)
      print ('N-1 fault on line to {:s}, line to {:s} out, filename {:s}'.format (case['tag'], val['tag'], root))
      prj.run()

  print ('Finished: {:.2f} seconds elapsed'.format(time.time() - start))


