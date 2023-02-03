# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: opendss_graph.py
""" Build and save a NetworkX graph of the OpenDSS feeder.

Paragraph.

Public Functions:
  :main: does the work
"""

import math
import sys
import networkx as nx
import json
import os
import csv
import pkg_resources

feederChoices = {
  'ieee9500':{'path':'models/ieee9500/', 'base':'Master-bal-initial-config.dss', 'network':'Network.json'},
  'ieee_lvn':{'path':'models/ieee_lvn/', 'base':'SecPar.dss', 'network':'Network.json'}
  }

kvbases = [0.208, 0.418, 0.48, 4.16, 12.47, 13.2, 13.8, 34.5, 69.0, 115.0, 138.0, 230.0]
def select_kvbase (val):
  kv = 12.47
  for i in range(len(kvbases)):
    err = abs(val/kvbases[i] - 1.0)
    if err < 0.02:
      kv = kvbases[i]
  return kv

def letter_phases (dss_phases):
  phs = ''
  if '1' in dss_phases:
    phs += 'A'
  if '2' in dss_phases:
    phs += 'B'
  if '3' in dss_phases:
    phs += 'C'
  return phs

def parse_bus_phases (busphs):
  idx = busphs.find('.')
  if idx >= 0:
    bus = busphs[:idx]
    phs = letter_phases (busphs[idx+1:])
  else:
    bus = busphs
    phs = 'ABC'
  return bus, phs

def dss_bus_phases (tok):
  bus = ''
  phs = ''
  if tok.startswith('bus1=') or tok.startswith('bus2='):
    bus, phs = parse_bus_phases (tok[5:])
  return bus, phs

def dss_transformer_xhl (tok):
  return float (dss_parm(tok))

def adjust_nominal_kv (kv, nphs, bDelta):
  if (nphs == 1) and not bDelta:
    kv *= math.sqrt(3.0)
  return kv

def add_row_to_class (dict, row, toks, strtoks):
  name = row[1].split('.')[1]
  if name not in dict:
    vals = {}
    for tok in toks:
      match = tok + '='
      for i in range(2, len(row)):
        if match in row[i]:
          parsed = row[i].partition('=')[2]
          if tok in strtoks:
            vals[tok] = parsed.lower()
          else:
            vals[tok] = float(parsed)
          break
    dict[name] = vals

def dict_from_file (fname, toks, strtoks):
  dict = {}
  if os.path.exists(fname):
    fp = open (fname, 'r')
    rdr = csv.reader (fp, delimiter=' ')
    for row in rdr:
      add_row_to_class (dict, row, toks, strtoks)
    fp.close()
  return dict

def count_bus_phases (bus):
  nph = 0
  for phs in ['.1', '.2', '.3']:
    if phs in bus:
      nph += 1
  if nph < 1:
    nph = 3
  return nph

def xfmr_dict_from_file (fname):
  dict = {}
  fp = open (fname, 'r')
  rdr = csv.reader (fp, delimiter=' ')
  for row in rdr:
    name = row[1].split('.')[1]
    if name not in dict:
      vals = {}
      inBuses = False
      for i in range(2, len(row)):
        if 'windings=' in row[i]:
          vals['windings'] = int(row[i].partition('=')[2])
        elif 'phases=' in row[i]:
          vals['phases'] = int(row[i].partition('=')[2])
        elif 'buses=[' in row[i]:
          inBuses = True
          vals['buses'] = []
          bus = row[i].partition('=[')[2].strip(',')
          vals['buses'].append(bus)
        elif inBuses:
          if ']' in row[i]:
            inBuses = False
          else:
            bus = row[i].strip(',')
            vals['buses'].append(bus)
      if 'windings' not in vals:
        vals['windings'] = len(vals['buses'])
      if 'phases' not in vals:
        vals['phases'] = count_bus_phases (vals['buses'][0])
      for i in range(len(vals['buses'])):
        vals['buses'][i] = vals['buses'][i].partition('.')[0]
      dict[name] = vals
  fp.close()
  return dict

def set_shunt_phasing (dict):
  for key, row in dict.items():
    if 'phases' not in row:
      row['phases'] = count_bus_phases(row['bus1'])
    else:
      row['phases'] = int(row['phases'])
    row['bus1'] = row['bus1'].partition('.')[0]

def set_branch_phasing (dict):
  for key, row in dict.items():
    if 'phases' not in row:
      row['phases'] = count_bus_phases(row['bus1'])
    else:
      row['phases'] = int(row['phases'])
    row['bus1'] = row['bus1'].partition('.')[0]
    row['bus2'] = row['bus2'].partition('.')[0]

def phases_ndata (phases):
  return {'phases':0, 'nomkv':0.0, 'loadkw': 0.0, 'genkva': 0.0, 'genkw': 0.0, 
    'pvkva': 0.0, 'pvkw': 0.0, 'batkva': 0.0, 'batkw': 0.0, 'batkwh': 0.0, 'capkvar': 0.0, 
    'shunts':[], 'source':False}

def xy_ndata (x, y):
  ndata = phases_ndata(0)
  ndata['x'] = x
  ndata['y'] = y
  return ndata

def update_node_phases (G, nd, phases):
  if 'ndata' not in G.nodes()[nd]:
    G.nodes()[nd]['ndata'] = phases_ndata(phases)
  else:
    oldphases = G.nodes()[nd]['ndata']['phases']
    G.nodes()[nd]['ndata']['phases'] = max (oldphases, phases)

def update_node_class (G, data, nclass):
  if data['bus1'] not in G.nodes():
    nph = 3
    if 'phases' in data:
      nph = data['phases']
    G.add_node (data['bus1'], nclass=nclass, ndata=phases_ndata(nph))
  else:
    G.nodes()[data['bus1']]['nclass'] = nclass
  return G.nodes()[data['bus1']]['ndata']

def make_opendss_graph(saved_path, outfile):
  #-----------------------
  # Pull Model Into Memory
  #-----------------------
  busxy = {}
  fp = open (os.path.join (saved_path, 'BusCoords.dss'), 'r')
  rdr = csv.reader (fp)
  for row in rdr:
    bus = row[0].lower()
    if bus not in busxy:
      busxy[bus] = {'x':float(row[1]),'y':float(row[2])}
  fp.close()

  sources = dict_from_file (os.path.join (saved_path, 'Vsource.dss'),
                            ['bus1', 'pu', 'R1', 'X1', 'R0', 'X0'],
                            ['bus1'])
  lines = dict_from_file (os.path.join (saved_path, 'Line.dss'),
                            ['bus1', 'bus2', 'units', 'Switch', 'length'],
                            ['bus1', 'bus2', 'units', 'Switch'])
  loads = dict_from_file (os.path.join (saved_path, 'Load.dss'),
                            ['bus1', 'phases', 'kV', 'kW'],
                            ['bus1'])
  generators = dict_from_file (os.path.join (saved_path, 'Generator.dss'),
                            ['bus1', 'kv', 'kW', 'kVA', 'pf'],
                            ['bus1'])
  capacitors = dict_from_file (os.path.join (saved_path, 'Capacitor.dss'),
                            ['bus1', 'kv', 'kvar', 'phases'], 
                            ['bus1'])
  solars = dict_from_file (os.path.join (saved_path, 'PVSystem.dss'),
                            ['bus1', 'kv', 'kVA', 'phases', 'Pmpp'], 
                            ['bus1'])
  batteries = dict_from_file (os.path.join (saved_path, 'Storage.dss'),
                            ['bus1', 'kv', 'kVA', 'phases', 'kWrated', 'kWhrated'], 
                            ['bus1'])
  reactors = dict_from_file (os.path.join (saved_path, 'Reactor.dss'),
                            ['bus1', 'bus2', 'R', 'X'], 
                            ['bus1', 'bus2'])
  regulators = dict_from_file (os.path.join (saved_path, 'RegControl.dss'),
                            ['transformer', 'winding', 'tapwinding', 'ptratio', 'vreg', 'band', 
                             'reversible', 'revvreg', 'revband','revThreshold', 'delay', 'revDelay'], 
                            ['transformer', 'reversible'])
  transformers = xfmr_dict_from_file (os.path.join (saved_path, 'Transformer.dss'))

  for key, row in regulators.items():
    transformers[row['transformer']]['regulator'] = True
  nswitch = 0
  for key, row in lines.items():
    if 'Switch' in row:
      if row['Switch'] == 'true':
        row['Switch'] = True
        nswitch += 1
      else:
        row['Switch'] = False
    else:
      row['Switch'] = False
  set_branch_phasing (lines)
  set_shunt_phasing (capacitors)
  set_shunt_phasing (solars)
  set_shunt_phasing (batteries)
  set_shunt_phasing (generators)
  set_shunt_phasing (loads)
  set_branch_phasing (reactors)

  load_kw = 0.0
  solar_kw = 0.0
  generator_kw = 0.0
  battery_kw = 0.0
  capacitor_kvar = 0.0
  for key, row in solars.items():
    solar_kw += row['Pmpp']
  for key, row in batteries.items():
    battery_kw += row['kWrated']
  for key, row in generators.items():
    generator_kw += row['kW']
  for key, row in loads.items():
    load_kw += row['kW']
  for key, row in capacitors.items():
    capacitor_kvar += row['kvar']
  print ('read {:4d} loads totalling      {:7.1f} kW'.format (len(loads), load_kw))
  print ('read {:4d} capacitors totalling {:7.1f} kvar'.format (len(capacitors), capacitor_kvar))
  print ('read {:4d} generators totalling {:7.1f} kW'.format (len(generators), generator_kw))
  print ('read {:4d} solars totalling     {:7.1f} kW'.format (len(solars), solar_kw))
  print ('read {:4d} batteries totalling  {:7.1f} kW'.format (len(batteries), battery_kw))

  print ('read {:4d} transformers'.format (len(transformers)))
  print ('read {:4d} regulators (as transformers)'.format (len(regulators)))
  print ('read {:4d} lines'.format (len(lines)))
  print ('read {:4d} switches (as lines)'.format (nswitch))
  print ('read {:4d} reactors'.format (len(reactors)))
  print ('read {:4d} sources'.format (len(sources)))
  print ('read {:4d} busxy'.format (len(busxy)))

  # construct a graph of the model, starting with all known buses that have XY coordinates
  G = nx.Graph()
  for key, data in busxy.items():
    G.add_node (key, nclass='bus', ndata=xy_ndata (data['x'], data['y']))

  # add series power delivery branches (not handling series capacitors)
  for key, data in lines.items():
    if data['Switch']:
      eclass = 'switch'
    else:
      eclass = 'line'
    G.add_edge(data['bus1'],data['bus2'],eclass=eclass,ename=key,edata=data)
    update_node_phases (G, data['bus1'], data['phases'])
    update_node_phases (G, data['bus2'], data['phases'])

  for key, data in reactors.items():
    G.add_edge(data['bus1'],data['bus2'],eclass='reactor',ename=key,edata=data)
    update_node_phases (G, data['bus1'], data['phases'])
    update_node_phases (G, data['bus2'], data['phases'])

  for key, data in transformers.items():
    eclass = 'transformer'
    if 'regulator' in data:
      if data['regulator']:
        eclass = 'regulator'
    G.add_edge(data['buses'][0],data['buses'][1],eclass=eclass,ename=key,edata=data)
    update_node_phases (G, data['buses'][0], data['phases'])
    update_node_phases (G, data['buses'][1], data['phases'])
    if data['windings'] > 2:
      G.add_edge(data['buses'][0],data['buses'][2],eclass=eclass,ename=key,edata=data)
      update_node_phases (G, data['buses'][2], data['phases'])

  # add the shunt elements
  for key, data in sources.items():
    old = update_node_class (G, data, 'source')
    old['source'] = True
    old['shunts'].append ('vsource.{:s}'.format(key))

  for key, data in loads.items():
    old = update_node_class (G, data, 'load')
    old['phases'] = max (old['phases'], data['phases'])
    old['nomkv'] = max (old['nomkv'], data['kV'])
    old['loadkw'] += data['kW']
    old['shunts'].append ('load.{:s}'.format(key))

  for key, data in capacitors.items():
    old = update_node_class (G, data, 'capacitor')
    old['phases'] = max (old['phases'], data['phases'])
    old['nomkv'] = max (old['nomkv'], data['kv'])
    old['capkvar'] += data['kvar']
    old['shunts'].append ('capacitor.{:s}'.format(key))

  for key, data in generators.items():
    old = update_node_class (G, data, 'generator')
    old['phases'] = max (old['phases'], data['phases'])
    old['nomkv'] = max (old['nomkv'], data['kv'])
    old['genkw'] += data['kW']
    old['genkva'] += data['kVA']
    old['shunts'].append ('generator.{:s}'.format(key))

  for key, data in solars.items():
    old = update_node_class (G, data, 'solar')
    old['phases'] = max (old['phases'], data['phases'])
    old['nomkv'] = max (old['nomkv'], data['kv'])
    old['pvkw'] += data['Pmpp']
    old['pvkva'] += data['kVA']
    old['shunts'].append ('pvsystem.{:s}'.format(key))

  for key, data in batteries.items():
    old = update_node_class (G, data, 'storage')
    old['phases'] = max (old['phases'], data['phases'])
    old['nomkv'] = max (old['nomkv'], data['kv'])
    old['batkw'] += data['kWrated']
    old['batkwh'] += data['kWhrated']
    old['batkva'] += data['kVA']
    old['shunts'].append ('storage.{:s}'.format(key))

  # save the graph
  json_fp = open (outfile, 'w')
  json_data = nx.readwrite.json_graph.node_link_data(G)
  json.dump (json_data, json_fp, indent=2)
  json_fp.close()

def make_builtin_graph (feeder_name):
  if feeder_name not in feederChoices:
    print ('{:s} is not a built-in feeder choice'.format(feeder_name))
    print ('please choose from', feederChoices.keys())
    return None
  row = feederChoices[feeder_name]
  fname = pkg_resources.resource_filename (__name__, row['path'] + row['network'])

