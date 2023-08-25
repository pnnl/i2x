import sys
import math
import numpy as np
import networkx as nx
import json
import os
import i2x.mpow_utilities as mpow
import i2x.bes_upgrades as bes

from bes_cases import *

def list_neighboring_branches (G):
  nradial = 0
  nexcluded = 0
  ncmax = 0
  for n in G.nodes():
    ev = list(G.edges(nbunch=n, data=True))
    nb = len(ev)
    bExcluded = False
    contingencies = []
    if nb > ncmax:
      ncmax = nb
    if nb < 2:
      nradial += 1
      if ev[0][2]['edata']['npar'] < 2:
        nexcluded += 1
        bExcluded = True
    if not bExcluded:
      for br in ev:
        brnum = int(br[2]['ename'])
        scale = br[2]['edata']['scale']
        contingencies.append ({'branch': brnum, 'scale': scale})
    print ('Node {:s}, Adj {:d}, Contingencies {:s}'.format (str(n), nb, str(contingencies)))
  print ('Max Adjacency Count = {:d}. There are {:d} radial buses, {:d} lacking a parallel circuit.'.format (ncmax, nradial, nexcluded))

if __name__ == '__main__':
  case_id = 0
  if len(sys.argv) > 1:
    case_id = int(sys.argv[1])
    if len(sys.argv) > 2:
      if int(sys.argv[2]) > 0:
        plot_labels = True
  sys_name = CASES[case_id]['name']
  d = mpow.read_matpower_casefile ('{:s}_wmva.m'.format(sys_name))
  G = mpow.build_matpower_graph (d)
  list_neighboring_branches (G)


