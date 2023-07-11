import sys
import math
import networkx as nx
import json
import os
import matplotlib.pyplot as plt 
import matplotlib.lines as lines
import matplotlib.patches as patches

plt.rcParams['savefig.directory'] = os.getcwd()

nodeTypes = {
  'load':  {'color':'green', 'tag':'Load',  'size':15},
  'gen':   {'color':'red',   'tag':'Gen',   'size':20},
  'solar': {'color':'orange','tag':'Solar', 'size':30},
  'wind':  {'color':'blue',  'tag':'Wind',  'size':30},
  'bus':   {'color':'black', 'tag':'Bus',   'size':10}
  }

edgeTypes = {
  'transformer': {'color':'gray',    'tag':'Xfmr'},
  'series':      {'color':'magenta', 'tag':'Cap'},
  'lineEHV':     {'color':'red',     'tag':'EHV'},
  'lineHV':      {'color':'orange',  'tag':'HV'},
  'lineMV':      {'color':'blue',    'tag':'MV'}
  }

# global constants
SQRT3 = math.sqrt(3.0)
RAD_TO_DEG = 180.0 / math.pi
MVA_BASE = 100.0
lblDeltaY = 0.0 # 0.005

def reset_type_counts():
  for key, val in edgeTypes.items():
    val['count'] = 0
  for key, val in nodeTypes.items():
    val['count'] = 0

def filter_types_used(d):
  ret = {}
  for key, val in d.items():
    if val['count'] > 0:
      ret[key] = val
  return ret

def get_edge_highlights(data):
  weight = 1.0
  color = edgeTypes['lineMV']['color']
  if data['eclass'] == 'transformer':
    weight = 3.0
    color = edgeTypes['transformer']['color']
    edgeTypes['transformer']['count'] += 1
  elif data['eclass'] == 'series':
    weight = 20.0
    color = edgeTypes['series']['color']
    edgeTypes['series']['count'] += 1
  else: # 'line'
    kv = data['edata']['kv']
    weight = 1.5
    if kv > 344.0:
      color = edgeTypes['lineEHV']['color']
      edgeTypes['lineEHV']['count'] += 1
      if kv > 499.0:
        weight = 2.0
    elif kv >= 100.0:
      color = edgeTypes['lineHV']['color']
      edgeTypes['lineHV']['count'] += 1
      if kv > 229.0:
        weight = 2.0
    else:
      edgeTypes['lineMV']['count'] += 1
  return weight, color

def get_edge_color(eclass):
  if eclass in edgeTypes:
    edgeTypes[eclass]['count'] += 1
    return edgeTypes[eclass]['color']
  print ('unknown edge class', eclass)
  return 'black'

def get_edge_mnemonic(eclass):
  if eclass in edgeTypes:
    return edgeTypes[eclass]['tag']
  return 'Unknown'

def get_node_size(nclass):
  if nclass in nodeTypes:
    return nodeTypes[nclass]['size']
  return 3

def get_node_color(nclass):
  if nclass in nodeTypes:
    nodeTypes[nclass]['count'] += 1
    return nodeTypes[nclass]['color']
  return 'black'

def get_node_mnemonic(nclass):
  if nclass in nodeTypes:
    return nodeTypes[nclass]['tag']
  return 'Unknown'

def plot_hca_graph (G, sys_name, case_name, plot_labels, buses, branches):
  reset_type_counts()
  plotNodes = []
  nodeColors = []
  nodeSizes = []
  max_hc = 0.0
  max_muF = 0.0
  for key, val in buses.items():
    if val > max_hc:
      max_hc = val
  for key, val in branches.items():
    if val > max_muF:
      max_muF = val

  for n in G.nodes():
    plotNodes.append(n)
    nodeColors.append ('green')
    hc = buses[n]
    hc_size = 200.0 * hc / max_hc
    nodeSizes.append (hc_size)

  # assign edge colors
  plotEdges = []
  edgeWidths = []
  edgeColors = []
  for n1, n2, data in G.edges(data=True):
    plotEdges.append ((n1, n2))
    ename = data['ename']
    muF = branches[ename]
    mva = data['edata']['rating']
    npar = data['edata']['npar']
    width = 2.0
    congestion = muF / max_muF
    red = congestion
    green = 0.0
    blue = 1.0 - congestion
    color = (red, green, blue)
    edgeWidths.append (width)
    edgeColors.append (color)

  # construct XY coordinates for plotting the network
  xy = {}
  xyLbl = {}
  lblNode = {}
  bMissing = False
  for n, data in G.nodes(data=True):
    ndata = data['ndata']
    if ('x' in ndata) and ('y' in ndata):
      busx = float(ndata['x'])
      busy = float(ndata['y'])
      xy[n] = [busx, busy]
      lblNode[n] = n.upper()
      xyLbl[n] = [busx, busy + lblDeltaY]
    else:
      bMissing = True
      break
  if bMissing:
    print ('Missing some node XY data, generating default coordinates')
    xy = nx.kamada_kawai_layout (G, weight='km')

  # create the plot
  fig, ax = plt.subplots(figsize=(10,8))

  nx.draw_networkx_nodes (G, xy, nodelist=plotNodes, node_color=nodeColors, node_size=nodeSizes, ax=ax)
  nx.draw_networkx_edges (G, xy, edgelist=plotEdges, edge_color=edgeColors, width=edgeWidths, alpha=0.8, ax=ax)
  if plot_labels:
    nx.draw_networkx_labels (G, xyLbl, lblNode, font_size=8, font_color='k', horizontalalignment='left', 
                             verticalalignment='baseline', ax=ax)

  plt.title ('{:s} Network, {:s} case, Max Hosting Capacity={:.3f} GW, Max Branch muF={:.3f}'.format(sys_name, case_name, max_hc, max_muF))
  plt.xlabel ('X coordinate')
  plt.ylabel ('Y coordinate')
  ax.grid(linestyle='dotted')
  xdata = [0, 1]
  ydata = [1, 0]
  legendEdges = filter_types_used (edgeTypes)
  legendNodes = filter_types_used (nodeTypes)
  lns = [lines.Line2D(xdata, ydata, color=get_edge_color(e)) for e in legendEdges] + \
    [lines.Line2D(xdata, ydata, color=get_node_color(n), marker='o') for n in legendNodes]
  labs = [get_edge_mnemonic (e) for e in legendEdges] + [get_node_mnemonic (n) for n in legendNodes]
  ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
  ax.legend(lns, labs, loc='lower left')
  plt.show()

def plot_system_graph (G, sys_name, plot_labels):
  reset_type_counts()
  # assign node colors
  plotNodes = []
  nodeColors = []
  nodeSizes = []
  for n in G.nodes():
    if 'nclass' in G.nodes()[n]:
      nclass = G.nodes()[n]['nclass']
    else:
      nclass = 'bus'
    plotNodes.append(n)
    nodeColors.append (get_node_color (nclass))
    nodeSizes.append (get_node_size (nclass))

  # assign edge colors
  plotEdges = []
  edgeWidths = []
  edgeColors = []
  for n1, n2, data in G.edges(data=True):
    plotEdges.append ((n1, n2))
    width, color = get_edge_highlights (data)
    edgeWidths.append (width)
    edgeColors.append (color)

  # construct XY coordinates for plotting the network
  xy = {}
  xyLbl = {}
  lblNode = {}
  bMissing = False
  for n, data in G.nodes(data=True):
    ndata = data['ndata']
    if ('x' in ndata) and ('y' in ndata):
      busx = float(ndata['x'])
      busy = float(ndata['y'])
      xy[n] = [busx, busy]
      lblNode[n] = n.upper()
      xyLbl[n] = [busx, busy + lblDeltaY]
    else:
      bMissing = True
      break
  if bMissing:
    print ('Missing some node XY data, generating default coordinates')
    xy = nx.kamada_kawai_layout (G, weight='km')

  # create the plot
  fig, ax = plt.subplots(figsize=(10,8))

  nx.draw_networkx_nodes (G, xy, nodelist=plotNodes, node_color=nodeColors, node_size=nodeSizes, ax=ax)
  nx.draw_networkx_edges (G, xy, edgelist=plotEdges, edge_color=edgeColors, width=edgeWidths, alpha=0.8, ax=ax)
  if plot_labels:
    nx.draw_networkx_labels (G, xyLbl, lblNode, font_size=8, font_color='k', horizontalalignment='left', 
                             verticalalignment='baseline', ax=ax)

  plt.title ('{:s} Network'.format(sys_name))
  plt.xlabel ('X coordinate')
  plt.ylabel ('Y coordinate')
  ax.grid(linestyle='dotted')
  xdata = [0, 1]
  ydata = [1, 0]
  legendEdges = filter_types_used (edgeTypes)
  legendNodes = filter_types_used (nodeTypes)
  lns = [lines.Line2D(xdata, ydata, color=get_edge_color(e)) for e in legendEdges] + \
    [lines.Line2D(xdata, ydata, color=get_node_color(n), marker='o') for n in legendNodes]
  labs = [get_edge_mnemonic (e) for e in legendEdges] + [get_node_mnemonic (n) for n in legendNodes]
  ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
  ax.legend(lns, labs, loc='lower left')
  plt.show()

def load_system_graph (fname):
  lp = open (fname).read()
  mdl = json.loads(lp)
  G = nx.readwrite.json_graph.node_link_graph(mdl)
  return G

def load_hca_results (case_name):
  buses = {}
  branches = {}
  fp = open ('{:s}.txt'.format(case_name), 'r')
  lines = fp.readlines()
  inBuses = False
  inBranches = False
  for ln in lines:
    if 'hca    wind   solar' in ln:
      inBuses = True
    elif 'Branches Overloaded' in ln:
      inBuses = False
    elif 'idx From   To     muF' in ln:
      inBranches = True
    else:
      toks = ln.strip().split()
      if inBuses:
        buses[toks[0]] = float(toks[1])
      elif inBranches:
        branches[toks[0]] = float(toks[3])
  fp.close()
  return buses, branches

if __name__ == '__main__':
  case_id = 0
  plot_labels = False
  sys_name = 'hca'
  case_name = 'hca_all'
  buses, branches = load_hca_results (case_name)
#  print (buses)
#  print (branches)
  if len(sys.argv) > 1:
    sys_name = sys.argv[1]
    if len(sys.argv) > 2:
      if int(sys.argv[2]) > 0:
        plot_labels = True
  G = load_system_graph ('{:s}_network.json'.format(sys_name))
  plot_hca_graph (G, sys_name, case_name, plot_labels, buses, branches)


