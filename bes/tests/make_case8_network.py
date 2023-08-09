# Copyright (C) 2021-2023 Battelle Memorial Institute
# file: plot_case8.py, derived from TESP's make_case8.py
# instead of creating a PYPOWER-based TESP case, we want the
# bus coordinates, branch ratings, and topology for HCA visualizations

import json
import math
import random

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# some of the system modeling assumptions 
load_pf = 0.98
load_qf = math.sqrt(1.0 - load_pf * load_pf)
dispatch = 47799.4 / 105607.1

zones = [[1, "Houston", 0.1, 0.1],
     [2, "North", 0.1, 0.1],
     [3, "South", 0.1, 0.1],
     [4, "West", 0.1, 0.1]]

def find_bus(arr, n):
  for ln in arr:
    if ln[0] == n:
      return ln
  return None


def find_line(arr, n1, n2):
  for ln in arr:
    if '//' not in ln[0]:
      if int(ln[1]) == n1 and int(ln[2]) == n2:
        return ln
  return None


if __name__ == '__main__':
  #   name,bus1,bus2,kV,length[miles],#parallel,r1[Ohms/mile],x1[Ohms/mile],b1[MVAR/mile],ampacity,capacity[MW]
  dlines = np.genfromtxt('Lines8.csv', dtype=str, skip_header=1, delimiter=',')

  # bus,zone,lon,lat,load,gen,diff,caps
  dbuses = np.genfromtxt('Buses8.csv', dtype=[int, int, float, float, float, float, float, float],
               skip_header=1, delimiter=',')

  # idx,bus,mvabase,pmin,qmin,qmax,c2,c1,c0,fuel
  dunits = np.genfromtxt('Units8.csv', dtype=[('idx', int), ('bus', int), ('mvabase', float), ('pmin', float),
                        ('qmin', float), ('qmax', float), ('c2', float), ('c1', float),
                        ('c0', float), ('fuel', 'U16')],
               skip_header=0, names=True, delimiter=',')
# print('units')
# print(dunits)
# print ('buses')
# print (dbuses)
# print ('lines')
# print (dlines)

  lbl345 = {}
  e345 = set()
  n345 = set()
  graph = nx.Graph()
  for e in dlines:
    n1 = int(e[1])
    n2 = int(e[2])
    npar = int(e[5])
    graph.add_edge(n1, n2)
    n345.add(n1)
    n345.add(n2)
    lbl345[(n1, n2)] = e[0]
    e345.add((n1, n2, npar))

  print('There are', len(n345), 'EHV buses and', len(e345), 'EHV lines retained; ratio=', len(e345) / len(n345))

  # build the PYPOWER case
  swing_bus = -1
  ppcase = {'pf_dc': 0,
        'opf_dc': 1,
        'bus': [],
        'gen': [],
        'branch': [],
        'zones': zones,
        'areas': [],
        'gencost': [],
        'genfuel': [],
        'DSO': [],
        'UnitsOut': [],
        'BranchesOut': []}
  for n in n345:
    ln = find_bus(dbuses, n)
    bus1 = int(ln[0])  # HV bus
    zone = int(ln[1])  # zone number
    Pg = float(ln[5])
    if Pg > 0.0:
      if Pg > 34000.0 and swing_bus < 0:  # this should pick up bus number 1, which has the largest generation
        bustype = 3
        swing_bus = bus1
      else:
        bustype = 2
    else:
      bustype = 1
    Pd = float(ln[4])
    Sd = Pd / load_pf
    Qd = Sd * load_qf
    Qs = float(ln[7])
    ppcase['bus'].append([bus1, bustype, Pd, Qd, 0, Qs, 1, 1, 0, 345, zone, 1.1, 0.9, 0.0, 0.0])
    if Pd > 0.0:
      ppcase['DSO'].append([bus1, 'SUBSTATION' + str(bus1), 0.0, Pd, Qd, 1.0, random.randint(-3600, 3600)])
  Zbase = 345.0 * 345.0 / 100.0
  for (n1, n2, npar) in e345:
    ln = find_line(dlines, n1, n2)
    bus1 = int(ln[1])
    bus2 = int(ln[2])
    dist = float(ln[4])
    r1 = dist * float(ln[6]) / Zbase / npar
    x1 = dist * float(ln[7]) / Zbase / npar
    b1 = dist * float(ln[8]) * npar / 100.0
    rated = npar * float(ln[10])  # this is MW, not amps
    ppcase['branch'].append([bus1, bus2, r1, x1, b1, rated, rated, rated, 0.0, 0.0, 1, -360.0, 360.0])
  idx = 1
# print('Units')
  total_units = 0
# print('Idx B#     Sg     Pg   Pmin   Qmin   Qmax     c2     c1     c0  N Fuel')
  for ln in dunits:  ### disaggregation
    n1 = int(ln[1])
    Sg = float(ln[2])
    if ln[9] == 'wind':
      nunits = 1
    elif ln[9] == 'gas':
      nunits = int((Sg + 500.0) / 500.0)
    elif ln[9] == 'coal':
      nunits = int((Sg + 1000.0) / 1000.0)
    else:
      nunits = int((Sg + 2000.0) / 2000.0)
    total_units += nunits
    Sg /= nunits
    Pg = Sg * dispatch
    Pmin = float(ln[3]) / nunits
    Pmin = 0.05 * Sg
    Pmin = 0.0
    if Pg < Pmin:
      Pg = Pmin
    if n1 == swing_bus:
      #    print ('Setting Pg from {:.2f} to 0 at swing bus {:d}'.format (Pg, swing_bus))
      Pg = 0.0
    Qmin = float(ln[4]) / nunits
    Qmax = float(ln[5]) / nunits
    # these are typical cost coefficients [$,MW] for typical unit of this fuel type
    c2 = float(ln[6])
    c1 = float(ln[7])
    c0 = float(ln[8])

#    print('{:3d} {:2d} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f} {:8.5f} {:8.2f} {:8.2f} {:2d} {:s}'
#        .format(idx, n1, Sg, Pg, Pmin, Qmin, Qmax, c2, c1, c0, nunits, ln[9]))
    idx += 1
    #  for disaggregated units, we want to space the values +/- 10% around the mean
    if nunits > 1:
      step_c2 = 0.2 * c2 / (nunits - 1)
      step_c1 = 0.2 * c1 / (nunits - 1)
      step_c0 = 0.2 * c0 / (nunits - 1)
      c2 *= 0.9
      c1 *= 0.9
      c0 *= 0.9
    for i in range(nunits):
      #    print ('  c2={:8.5f} c1={:8.2f} c0={:8.2f}'.format (c2, c1, c0))
      ppcase['gen'].append([n1, Pg, 0.0, Qmax, Qmin, 1.0, Sg, 1, Sg, Pmin, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
      ppcase['gencost'].append([2, 0, 0, 3, c2, c1, c0])
      ppcase['genfuel'].append([ln[9]])
      if nunits > 1:
        c2 += step_c2
        c1 += step_c1
        c0 += step_c0
# print('{:d} total units'.format(total_units))

  ppcase['swing_bus'] = swing_bus

  # this would save the PYPOWER case
  #fp = open('ercot_8.json', 'w')
  #json.dump(ppcase, fp, indent=2)
  #fp.close()

# print('swing bus is', swing_bus)

  # draw the retained EHV network

  xy = {}
  lblbus345 = {}
  for b in dbuses:
    xy[b[0]] = [b[2], b[3]]
    if b[0] in n345:
      lblbus345[b[0]] = str(b[0]) + ':' + str(int(b[6]))

  lst345 = []
  w345 = []
  for (n1, n2, npar) in e345:
    lst345.append((n1, n2))
    w345.append(2.0 * npar)

# fig, ax = plt.subplots()
#
# nx.draw_networkx_nodes(graph, xy, nodelist=list(n345), node_color='k', node_size=80, alpha=0.3, ax=ax)
# nx.draw_networkx_edges(graph, xy, edgelist=lst345, edge_color='r', width=w345, alpha=0.8, ax=ax)
# nx.draw_networkx_labels(graph, xy, lblbus345, font_size=12, font_color='b', ax=ax)
#
# plt.title('Graph of Retained EHV Lines')
# plt.xlabel('Longitude [deg]')
# plt.ylabel('Latitude [deg N]')
# plt.grid(linestyle='dotted')
# ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
# plt.show()

  # here we save the HCA layout, not considering transformers or series capacitors
  wind_buses = []
  for row in dunits:
    if row[9] == 'wind':
      wind_buses.append(str(row[1]))
  print ('wind generation at buses', wind_buses)
  G = nx.Graph()
  for row in dbuses:
    nclass = 'gen'
    key = str(row[0])
    if key in wind_buses:
      nclass = 'wind'
    G.add_node (str(row[0]), nclass=nclass, ndata={'kv':345.0,'x':row[2],'y':row[3]})
  key = 1
  for row in dlines:
    km = round(1.609*float(row[4]),3)
    weight = round(0.001*km,4)
    npar = int(row[5])
    mva = float(row[10]) * npar
    kv = float(row[3])
    G.add_edge(row[1],row[2],eclass='line',ename=str(key), edata={'km':km, 
                                                                  'kv':float(row[3]),
                                                                  'npar':npar,
                                                                  'rating':mva}, weight=weight)
    key += 1

  fp = open ('hca_network.json', 'w')
  gdata = nx.readwrite.json_graph.node_link_data(G)
  json.dump (gdata, fp, indent=2)
  fp.close()


