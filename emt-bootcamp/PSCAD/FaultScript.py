# Copyright (C) 2023 Battelle Memorial Institute
# file: FaultScript.py
""" Automating faults in PSCAD for the EMT bootcamp.

Preconditions:
1) PSCAD has been launched
2) Solar4 project has been loaded into PSCAD
3) The time step and simulation time have been set
4) Components to be modified have been assigned unique names
"""

import mhi.pscad

# one row for each case
#  'tag' codes the phases involved and expected retained voltage
#  'L' is the fault inductance in Henries
cases = [
  {'tag':'abcg80', 'L':0.1057},
  {'tag':'abcg50', 'L':0.0264},
  {'tag':'abcg25', 'L':0.0088},
  {'tag':'abcg01', 'L':0.0001},
  {'tag':'ag80', 'L':0.1057},
  {'tag':'ag50', 'L':0.0264},
  {'tag':'ag25', 'L':0.0088},
  {'tag':'ag01', 'L':0.0001},
  {'tag':'bc80', 'L':0.1057},
  {'tag':'bc50', 'L':0.0264},
  {'tag':'bc25', 'L':0.0088},
  {'tag':'bc01', 'L':0.0001}
]

if __name__ == '__main__':
  # verify the preconditions
  pscad = mhi.pscad.application()
  s = pscad.settings()
  print ('Version:', pscad.version)
  print ('Dictionary of projects currently loaded:', pscad.projects())
  prj = pscad.project('Solar4')
  print ('Fault automation project:', prj)

  # interfaces to components that will be modified
  faultL = prj.find_first(Name='FaultL')
  fault = prj.find_first(Name='Fault')
  recorder = prj.find_first(Name='Recorder')

  if False: # for discovery of settable component parameters
    print ('Fault parameters:', fault.parameters())
    print ('Inductor parameters:', faultL.parameters())
    print ('Recorder parameters:', recorder.parameters())

  # table-driven parametric study
  for row in cases:
    faultL.parameters (L=row['L'])
    recorder.parameters (FName=row['tag'])
    A=False
    B=False
    C=False
    G=False
    if 'a' in row['tag']:
      A=True
    if 'b' in row['tag']:
      B=True
    if 'c' in row['tag']:
      C=True
    if 'g' in row['tag']:
      G=True
    fault.parameters (A=A, B=B, C=C, G=G)
    prj.run()

