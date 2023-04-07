# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: plot_opendss_feeder.py
""" Plots the OpenDSS feeder from a JSON file

Reads the feeder components and coordinates from a Network.json file.
Creates Network.pdf high-quality plot, then shows a screen plot that may be saved to PNG.

Network.json is output from opendss_graph.py.  It contains a networkx graph,
with supplemental node and link data to describe the OpenDSS components. In this file,
a node is as defined by networkx, not as defined by OpenDSS.

The node id is the OpenDSS bus name, and the node ndata is:

- shunts (str): an array of fully-qualified names of loads, capacitors and DER attached to this node
- nomkv (float): nominal line-to-line voltage [kV] at this location, if known
- loadkw (float): total load kw at this node
//- loadkvar (float): total load kvar at this node
- capkvar (float): total kvar of shunt capacitors at this node
- pvkva (float): the total kva of all PV at this node
- pvkw (float): the total kw (Pmpp) of all PV at this node
- genkva (float): the total kva of all generators at this node
- genkw (float): the total kw of all generators at this node
- batkva (float): the total kva of all storage at this node
- batkw (float): the total kw of all storage at this node
- batkwh (float): the total kwh of all storage at this node
- source (boolean): true only if the circuit source is connected here
- x (float): horizontal coordinate of this node location, arbitrary units
- y (float): vertical coordinate of this node location, arbitrary units
- phases (int): number of phases at this bus, 1..3

The link data is:

- eclass (str): the OpenDSS class name, line or transformer
- ename (str): the OpenDSS instance name, with its class
- source (str): the node id corresponding to bus1 from OpenDSS
- target (str): the node id corresponding to bus2 from OpenDSS

The edata for each line link may contain:

//- r1 (float): positive sequence resistance, in Ohms
//- x1 (float): positive sequence reactance, in Ohms
//- r0 (float): zero sequence resistance, in Ohms
//- x0 (float): zero sequence reactance, in Ohms
//- c1 (float): positive sequence capacitance, in nF
//- c0 (float): zero sequence capacitance, in nF
- len (float): length of the line, in km. This may be zero for a switch.
- phases (int): number of phases in this link, 1..3

The edata for each transformer link may contain:

//- phs1 (str): include A, B, and/or C if those phases are present on the primary
//- phs2 (str): include A, B, and/or C if those phases are present on the secondary
//- conn1 (str): w if the primary is wye, d if delta
//- conn2 (str): w if the secondary is wye, d if delta
//- kv1 (float): primary winding kV rating, line-to-neutral for single-phase, line-to-line otherwise
//- kv2 (float): secondary winding kV rating, line-to-neutral for single-phase, line-to-line otherwise
//- kva1 (float): kva rating of the primary
//- kva2 (float): kva rating of the secondary
//- xhl (float): percent reactance
//- r1 (float): equivalent positive sequence resistance, in Ohms from the primary
//- x1 (float): equivalent positive sequence reactance, in Ohms from the primary
//- r0 (float): equivalent zero sequence resistance, in Ohms from the primary
//- x0 (float): equivalent zero sequence reactance, in Ohms from the primary
//- phases (str): include A, B, and/or C if those phases are present in this link

Consult the networkx module documentation for more information about the json file format.

Public Functions:
  :main: does the work

Args:
  arg1 (str): base file name, don't add the extension, defaults to ReducedNetwork
  arg2 (int): choose 1 to include text node labels (default), or 0 not to

Returns:
  str: writes information and warnings about missing nodes or edges to the console
"""

import json
import matplotlib.pyplot as plt 
import matplotlib.lines as lines
import matplotlib.patches as patches
import networkx as nx
import sys
import csv
import pkg_resources

feederChoices = {
  'ieee9500':{'path':'models/ieee9500/', 'base':'Master-bal-initial-config.dss', 'network':'Network.json'},
  'ieee_lvn':{'path':'models/ieee_lvn/', 'base':'SecPar.dss', 'network':'Network.json'}
  }

lblDeltaY = 0.0 # 0.35

edgeTypes = {
  'line':        {'color':'gray',   'tag':'LN'},
  'transformer': {'color':'orange', 'tag':'XFM'},
  'regulator':   {'color':'red',    'tag':'REG'},
  'switch':      {'color':'blue',   'tag':'SWT'},
  'nwp':         {'color':'magenta','tag':'NWP'},
  'reactor':     {'color':'green',  'tag':'RCT'}
  }

nodeTypes = {
  'source':     {'color':'cyan',   'tag':'SUB', 'size':10, 'lblDeltaY': -lblDeltaY},
  'generator':  {'color':'red',    'tag':'GEN', 'size':10, 'lblDeltaY':  lblDeltaY},
  'solar':      {'color':'gold',   'tag':'PV',  'size':25, 'lblDeltaY': -lblDeltaY},
  'capacitor':  {'color':'blue',   'tag':'CAP', 'size':15, 'lblDeltaY': -lblDeltaY},
  'storage':    {'color':'green',  'tag':'BAT', 'size':35, 'lblDeltaY': -lblDeltaY}
  }

def get_node_mnemonic(nclass):
  if nclass in nodeTypes:
    return nodeTypes[nclass]['tag']
  return nodeTypes['other']['tag']

def get_node_size(nclass):
  if nclass in nodeTypes:
    return nodeTypes[nclass]['size']
  return 3

def get_node_offset(nclass):
  if nclass in nodeTypes:
    return nodeTypes[nclass]['lblDeltaY']
  return -lblDeltaY

def get_node_color(nclass):
  if nclass in nodeTypes:
    return nodeTypes[nclass]['color']
  return 'black'

def get_edge_width(nphs):
  if nphs == 1:
    return 2.0 # 1.0
  if nphs == 2:
    return 2.0 # 1.5
  return 2.0

def get_edge_color(eclass):
  if eclass in edgeTypes:
    return edgeTypes[eclass]['color']
  print ('unknown edge class', eclass)
  return edgeTypes['unknown']['color']

def get_edge_mnemonic(eclass):
  if eclass in edgeTypes:
    return edgeTypes[eclass]['tag']
  return edgeTypes['unknown']['tag']

def load_opendss_graph (json_name):
  lp = open (json_name).read()
  feeder = json.loads(lp)
  G = nx.readwrite.json_graph.node_link_graph(feeder)
#  nbus = G.number_of_nodes()
#  nbranch = G.number_of_edges()
#  print ('read graph with', nbus, 'nodes and', nbranch, 'edges')
  return G

def load_builtin_graph (feeder_name):
  if feeder_name not in feederChoices:
    print ('{:s} is not a built-in feeder choice'.format(feeder_name))
    print ('please choose from', feederChoices.keys())
    return None
  row = feederChoices[feeder_name]
  fname = pkg_resources.resource_filename (__name__, row['path'] + row['network'])
  return load_opendss_graph (fname)

def plot_opendss_feeder (G, plot_labels = False, pdf_name = None, fig = None, ax = None, title=None, on_canvas=False):

  # extract the XY coordinates available for plotting
  xy = {}
  xyLbl = {}
  lblNode = {}
  plotNodes = []
  nodeColors = []
  nodeSizes = []
  for n in G.nodes():
    if 'ndata' in G.nodes()[n]:
      ndata = G.nodes()[n]['ndata']
      if 'x' in ndata:
        busx = float(ndata['x']) / 1000.0
        busy = float(ndata['y']) / 1000.0
        xy[n] = [busx, busy]
        if 'nclass' in G.nodes()[n]:
          nclass = G.nodes()[n]['nclass']
          bLabel = False
          if nclass == 'source':
            bLabel = True
          if nclass == 'storage' and ndata['batkva'] >= 100.0:
            bLabel = True
          if nclass == 'generator' and ndata['genkva'] >= 100.0:
            bLabel = True
          if nclass == 'solar' and ndata['pvkva'] >= 100.0:
            bLabel = True
          if bLabel and (n not in lblNode):
            lblNode[n] = n.upper()
            xyLbl[n] = [busx, busy + get_node_offset (nclass)]
        else:
          nclass = 'bus'
        plotNodes.append(n)
        nodeColors.append (get_node_color (nclass))
        nodeSizes.append (get_node_size (nclass))

  # only plot the edges that have XY coordinates at both ends
  plotEdges = []
  edgeWidths = []
  edgeColors = []
  for n1, n2, data in G.edges(data=True):
    bFound = False
    if n1 in xy:
      if n2 in xy:
        bFound = True
        nph = data['edata']['phases']
        plotEdges.append ((n1, n2))
        edgeWidths.append (get_edge_width(nph))
        edgeColors.append (get_edge_color(data['eclass']))
    if not bFound:
      print ('unable to plot', data['ename'])

  if fig is None:
    fig, ax = plt.subplots()
  nx.draw_networkx_nodes (G, xy, nodelist=plotNodes, node_color=nodeColors, node_size=nodeSizes, ax=ax)
  nx.draw_networkx_edges (G, xy, edgelist=plotEdges, edge_color=edgeColors, width=edgeWidths, alpha=0.8, ax=ax)
  if plot_labels:
#    print ('plotting {:d} node labels'.format (len(lblNode)))
    nx.draw_networkx_labels (G, xyLbl, lblNode, font_size=8, font_color='k', 
                 horizontalalignment='left', verticalalignment='baseline', ax=ax)
  if title is not None:
    plt.title (title)
  plt.xlabel ('X coordinate [k]')
  plt.ylabel ('Y coordinate [k]')
  ax.grid(linestyle='dotted')
  xdata = [0, 1]
  ydata = [1, 0]
  lns = [lines.Line2D(xdata, ydata, color=get_edge_color(e)) for e in edgeTypes] + \
    [lines.Line2D(xdata, ydata, color=get_node_color(n), marker='o') for n in nodeTypes]
  labs = [get_edge_mnemonic (e) for e in edgeTypes] + [get_node_mnemonic (n) for n in nodeTypes]
  ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
  ax.legend(lns, labs, loc='lower right')
  if pdf_name is not None:
    plt.savefig (pdf_name)
  if not on_canvas:
    plt.show()

def get_der_kw (load_kw):
  kw = 5.0 * round(load_kw/5.0)
  if kw < 5.0:
    kw = 3.0
  return kw

def get_first_shunt_name (shunts, nclass):
  for row in shunts:
    toks = row.split('.')
    if toks[0] == nclass:
      return toks[1]
  return '**NOT FOUND**'

def parse_opendss_graph (G, bSummarize=True):
  pvder = {}
  gender = {}
  batder = {}
  largeder = {}
  resloads = {}
  loadkw = 0.0

  for n in G.nodes():
    if 'ndata' in G.nodes()[n] and 'nclass' in G.nodes()[n]:
      ndata = G.nodes()[n]['ndata']
      nclass = G.nodes()[n]['nclass']
      bus = n
      nomkv = ndata['nomkv']
      phases = ndata['phases']
      loadkw += ndata['loadkw']
      if nclass == 'solar':
        kva = ndata['pvkva']
        key = get_first_shunt_name (ndata['shunts'], 'pvsystem')
        pvder[key] = {'bus':bus, 'kv':nomkv, 'kva':kva, 'kw':ndata['pvkw'], 'phases':phases}
        if kva >= 100.0:
          largeder[key] = {'bus':bus, 'kv':nomkv, 'kva':kva, 'kw':ndata['pvkw'], 'phases':phases, 'type':'solar'}
      elif nclass == 'generator':
        kva = ndata['genkva']
        key = get_first_shunt_name (ndata['shunts'], 'generator')
        gender[key] = {'bus':bus, 'kv':nomkv, 'kva':kva, 'kw':ndata['genkw'], 'phases':phases}
        if kva >= 100.0:
          largeder[key] = {'bus':bus, 'kv':nomkv, 'kva':kva, 'kw':ndata['genkw'], 'phases':phases, 'type':'generator'}
      elif nclass == 'storage':
        kva = ndata['batkva']
        key = get_first_shunt_name (ndata['shunts'], 'storage')
        batder[key] = {'bus':bus, 'kv':nomkv, 'kva':kva, 'kw':ndata['batkw'], 'phases':phases}
        if kva >= 100.0:
          largeder[key] = {'bus':bus, 'kv':nomkv, 'kva':kva, 'kw':ndata['batkw'], 'phases':phases, 'type':'storage'}
      elif nclass == 'load':
        kw = ndata['loadkw']
        if (phases == 2) and (nomkv < 1.0):
          key = get_first_shunt_name (ndata['shunts'], 'load')
          resloads[key] = {'bus':bus, 'kv':nomkv, 'kva':kva, 'phases': phases, 'derkw': get_der_kw(kw)}

  if bSummarize:
    print ('\nLARGE_DER')
    for key, row in largeder.items():
      print (key, row)
    print ('\nPV_DER', len(pvder))
    print ('\nGEN_DER', len(gender))
    print ('\nBAT_DER', len(batder))
    print ('\nROOFTOP CANDIDATES', len(resloads))
    print ('\bTOTAL LOAD KW = {:.2f}'.format(loadkw))

  return pvder, gender, batder, largeder, resloads, loadkw
