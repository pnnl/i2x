# Copyright (C) 2017-2023 Battelle Memorial Institute
# file: der_choices.py
"""Configuration data for DER test feeders
"""

# TODO: consider migration to a JSON file for customization

feederChoices = {
  'ieee9500':{'path':'models/ieee9500/', 'base':'Master-bal-initial-config.dss', 'network':'Network.json'},
  'ieee_lvn':{'path':'models/ieee_lvn/', 'base':'SecPar.dss', 'network':'Network.json'},
  'radial':{'path':'models/radial/', 'base':'HCABase.dss', 'network':'Network.json'}
  }

solarChoices = {
  'pclear':{'dt':1.0, 'file':'pclear.dat', 'npts':0, 'data':None},
  'pcloud':{'dt':1.0, 'file':'pcloud.dat', 'npts':0, 'data':None},
  'pvduty':{'dt':1.0, 'file':'pvloadshape-1sec-2900pts.dat', 'npts':0, 'data':None}
  }

# this is the original OpenDSS data for piece-wise constant interpolation
#  we are now using a quadratic interpolant at 1-second interfals
#'default':{'t':[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24],
#           'p':[0.677,0.6256,0.6087,0.5833,0.58028,0.6025,0.657,0.7477,0.832,0.88,0.94,0.989,0.985,0.98,0.9898,0.999,1,0.958,0.936,0.913,0.876,0.876,0.828,0.756,0.677]},

loadChoices = {
  'qdaily':{'dt':1.0, 'file':'qdaily.dat', 'npts':0, 'data':None},
  'ldaily':{'dt':1.0, 'file':'ldaily.dat', 'npts':0, 'data':None},
  'cdaily':{'dt':1.0, 'file':'cdaily.dat', 'npts':0, 'data':None},
  'flat':{'t':[0,24], 'p':[1.0, 1.0]}
  }

inverterChoices = {
  'CONSTANT_PF':{'v':[0.90,1.10],
                 'p':[1.00,1.00],
                 'q':[0.00,0.00]},
  'VOLT_WATT':{'v':[0.90,1.06,1.10],
               'p':[1.00,1.00,0.20],
               'q':[0.00,0.00,0.00]}, 
  'VOLT_VAR_CATA':{'v':[0.90,1.10],
                   'p':[1.00,1.00],
                   'q':[0.25,-.25]},
  'VOLT_VAR_CATB':{'v':[0.90,0.92,0.98,1.02,1.08,1.10],
                   'p':[1.00,1.00,1.00,1.00,1.00,1.00],
                   'q':[0.44,0.44,0.00,0.00,-.44,-.44]},
  'VOLT_VAR_AVR':{'v':[0.90,0.98,1.02,1.10],
                  'p':[1.00,1.00,1.00,1.00],
                  'q':[0.44,0.44,-.44,-.44]}, 
  'VOLT_VAR_VOLT_WATT':{'v':[0.90,0.92,0.98,1.02,1.06,1.08,1.10],
                        'p':[1.00,1.00,1.00,1.00,1.00,0.60,0.20],
                        'q':[0.44,0.44,0.00,0.00,-.2933,-.44,-.44]},
  'VOLT_VAR_14H':{'v':[0.90,0.94,0.97,1.03,1.06,1.10],
                  'p':[1.00,1.00,1.00,1.00,1.00,0.00],
                  'q':[0.44,0.44,0.00,0.00,-.44,-.44]}
  }

solutionModeChoices = ['SNAPSHOT', 'DAILY', 'DUTY']#, 'YEARLY']
controlModeChoices = ['OFF', 'STATIC'] #, 'TIME', 'EVENT']

