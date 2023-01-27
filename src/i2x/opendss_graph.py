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

kvbases = [0.208, 0.418, 0.48, 4.16, 12.47, 13.2, 13.8, 34.5, 69.0, 115.0, 138.0, 230.0]
def select_kvbase (val):
  kv = 12.47
  for i in range(len(kvbases)):
    err = abs(val/kvbases[i] - 1.0)
    if err < 0.02:
      kv = kvbases[i]
  return kv

def is_node_class(cls):
  if cls == 'load':
    return True
  if cls == 'capacitor':
    return True
  if cls == 'pvsystem':
    return True
  if cls == 'vsource':
    return True
  if cls == 'circuit':
    return True
  return False

def get_nclass(nd):
  if nd == '0':
    return 'ground'
  return 'bus'

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

def dss_parm (tok):
  idx = tok.find('=')
  if idx >= 0:
    tok = tok[idx+1:]
  idx = tok.find('(')
  if idx >= 0:
    tok = tok[idx+1:]
  idx = tok.find(')')
  if idx >= 0:
    tok = tok[:idx]
  return tok.strip()

def dss_transformer_bus_phases (tok1, tok2):
  bus1, phs1 = parse_bus_phases (dss_parm(tok1))
  bus2, phs2 = parse_bus_phases (dss_parm(tok2))
  return bus1, bus2, phs1, phs2

def dss_transformer_conns (tok1, tok2):
  parm1 = dss_parm (tok1)
  parm2 = dss_parm (tok2)
  return parm1, parm2

def dss_transformer_kvas (tok1, tok2):
  parm1 = dss_parm (tok1)
  parm2 = dss_parm (tok2)
  return float (parm1), float (parm2)

def dss_transformer_kvs (tok1, tok2):
  parm1 = dss_parm (tok1)
  parm2 = dss_parm (tok2)
  return float (parm1), float (parm2)

def dss_transformer_xhl (tok):
  return float (dss_parm(tok))

def adjust_nominal_kv (kv, nphs, bDelta):
  if (nphs == 1) and not bDelta:
    kv *= math.sqrt(3.0)
  return kv

def merge_ndata(old, new): # not touching nomkv, x, y, busnum, dist, phases
  if new['kw'] != 0.0:
    old['kw'] += new['kw']
  if new['kvar'] != 0.0:
    old['kvar'] += new['kvar']
  if new['capkvar'] != 0.0:
    old['capkvar'] += new['capkvar']
  if new['derkva'] != 0.0:
    old['derkva'] += new['derkva']
  if new['source']:
    old['source'] = True
  old['shunts'].append (new['shunts'][0])
  return old

def merge_busmap(dssdata, row):
  dssdata['busnum'] = row['busnum']
  dssdata['x'] = row['x']
  dssdata['y'] = row['y']
  dssdata['phases'] = row['phases']  # TODO - accumulate these from parsing individual model lines?
  return dssdata

def format_ndata(ndata):
  ndata ['kw'] = float ('{:.3f}'.format (ndata['kw']))
  ndata ['kvar'] = float ('{:.3f}'.format (ndata['kvar']))
  ndata ['capkvar'] = float ('{:.3f}'.format (ndata['capkvar']))
  ndata ['derkva'] = float ('{:.3f}'.format (ndata['derkva']))
  ndata ['nomkv'] = select_kvbase (ndata['nomkv'])
  return ndata

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

def make_opendss_graph(saved_path, outfile):
  #-----------------------
  # Pull Model Into Memory
  #-----------------------
  busxy = {}
  fp = open (os.path.join (saved_path, 'BusCoords.dss'), 'r')
  rdr = csv.reader (fp)
  for row in rdr:
    bus = row[0]
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

  quit()

  # construct a graph of the model, starting with known links
  G = nx.Graph()
  for ln in lines:
    if ln[0] == 'new':
      toks = ln[1].split('.')
      dssclass = toks[0]
      dssname = toks[1]
      phases = ''
      n1 = '0'
      n2 = '0'
      dssdata = {}
      if is_node_class (dssclass):
        dssdata['shunts'] = ['{:s}.{:s}'.format (dssclass, dssname)]
        dssdata['nomkv'] = 0.0
        dssdata['kw'] = 0.0
        dssdata['kvar'] = 0.0
        dssdata['capkvar'] = 0.0
        dssdata['derkva'] = 0.0
        if (dssclass == 'vsource') or (dssclass == 'circuit'):
          dssdata['source'] = True
        else:
          dssdata['source'] = False
        bDelta = False
        for i in range(2,len(ln)):
          if ln[i].startswith('bus1='):
            n1, phases = dss_bus_phases (ln[i])
          elif ln[i].startswith('conn='):
            if 'd' in dss_parm(ln[i]):
              bDelta = True
          elif ln[i].startswith('kv='):
            dssdata['nomkv'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('kw=') and dssclass != 'storage':
            dssdata['kw'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('kvar='):
            if dssclass == 'capacitor':
              dssdata['capkvar'] = float (dss_parm(ln[i]))
            else:
              dssdata['kvar'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('kva='):
            dssdata['derkva'] = float (dss_parm(ln[i]))
        dssdata['phases'] = phases
        if 'nomkv' in dssdata:
          dssdata['nomkv'] = adjust_nominal_kv (dssdata['nomkv'], len(phases), bDelta)
        if n1 not in G.nodes():
          if n1 in busmap:
            dssdata = merge_busmap (dssdata, busmap[n1])
          G.add_node (n1, nclass=get_nclass(n1), ndata=format_ndata(dssdata))
        else:
          if 'ndata' in G.nodes()[n1]:
            dssdata = merge_ndata (G.nodes()[n1]['ndata'], dssdata)
          elif n1 in busmap:
            dssdata = merge_busmap (dssdata, busmap[n1])
          G.nodes()[n1]['ndata'] = format_ndata(dssdata)
      else:
        for i in range(2,len(ln)):
          if ln[i].startswith('bus1='):
            n1, phases = dss_bus_phases (ln[i])
          elif ln[i].startswith('bus2='):
            n2, phases = dss_bus_phases (ln[i])
          elif ln[i].startswith('buses='):  # TODO: handle transformers with more than 2 windings
            n1, n2, phs1, phs2 = dss_transformer_bus_phases (ln[i], ln[i+1])
            dssdata['phs1'] = phs1
            dssdata['phs2'] = phs2
            phases = phs1
          elif ln[i].startswith('conns='):
            conn1, conn2 = dss_transformer_conns (ln[i], ln[i+1])
            dssdata['conn1'] = conn1
            dssdata['conn2'] = conn2
          elif ln[i].startswith('kvs='):
            kv1, kv2 = dss_transformer_kvs (ln[i], ln[i+1])
            dssdata['kv1'] = kv1
            dssdata['kv2'] = kv2
          elif ln[i].startswith('kvas='):
            kva1, kva2 = dss_transformer_kvas (ln[i], ln[i+1])
            dssdata['kva1'] = kva1
            dssdata['kva2'] = kva2
          elif ln[i].startswith('xhl='):
            dssdata['xhl'] = dss_transformer_xhl (ln[i])
          elif ln[i].startswith('kw='):
            dssdata['kw'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('kvar='):
            dssdata['kvar'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('len='):
            dssdata['len'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('kv='):
            dssdata['kv'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('r1='):
            dssdata['r1'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('x1='):
            dssdata['x1'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('c1='):
            dssdata['c1'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('r0='):
            dssdata['r0'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('x0='):
            dssdata['x0'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('c0='):
            dssdata['c0'] = float (dss_parm(ln[i]))
          elif ln[i].startswith('conn='):
            dssdata['conn'] = dss_parm(ln[i])
        dssdata['phases'] = phases
        G.add_edge(n1,n2,eclass=dssclass,ename=dssname,edata=dssdata)

  # backfill missing node attributes
  # TODO: try to fill in the missing/zero nomkv values
  for n in G.nodes():
    if 'ndata' not in G.nodes()[n]:
      if n in busmap:
        row = busmap[n]
        dssdata = {'shunts':[], 'nomkv':0.0, 'kw':0.0, 'kvar':0.0, 'capkvar':0.0, 'derkva':0.0, 'source':False,
            'phases':row['phases'], 'busnum':row['busnum'], 'x':row['x'], 'y':row['y']}
        G.nodes()[n]['ndata'] = dssdata
      else:
        print ('cannot find node', n, 'in the busmap')

  # save the graph
  json_fp = open (root + '.json', 'w')
  json_data = nx.readwrite.json_graph.node_link_data(G)
  json.dump (json_data, json_fp, indent=2)
  json_fp.close()

