# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: plot_opendss_feeder.py
""" Plots the OpenDSS feeder from a JSON file

Reads the feeder components and coordinates from a local ReducedNetwork.json file.
Creates j1reduced.pdf high-quality plot, then shows a screen plot that may be saved to PNG.

ReducedNetwork.json is output from RunReduction.py.  It contains a networkx graph,
with supplemental node and link data to describe the OpenDSS components. In this file,
a node is as defined by networkx, not as defined by OpenDSS.

The node id is the OpenDSS bus name, and the node ndata is:

- shunts (str): an array of fully-qualified names of loads, capacitors and DER attached to this node
- nomkv (float): nominal line-to-line voltage [kV] at this location, if known
- kw (float): total load kw at this node
- kvar (float): total load kvar at this node
- capkvar (float): total kvar of shunt capacitors at this node
- derkva (float): the total kva of DER (all PV in this project) at this node
- source (boolean): true only if the circuit source is connected here
- phase (str): include a, b, and/or c if those phases are present at this node
- busnum (int): the sequential bus number of this node in the corresponding ATP model
- x (float): horizontal coordinate of this node location, arbitrary units
- y (float): vertical coordinate of this node location, arbitrary units

The link data is:

- eclass (str): the OpenDSS class name, line or transformer
- ename (str): the OpenDSS instance name, with its class
- source (str): the node id corresponding to bus1 from OpenDSS
- target (str): the node id corresponding to bus2 from OpenDSS

The edata for each line link may contain:

- r1 (float): positive sequence resistance, in Ohms
- x1 (float): positive sequence reactance, in Ohms
- r0 (float): zero sequence resistance, in Ohms
- x0 (float): zero sequence reactance, in Ohms
- c1 (float): positive sequence capacitance, in nF
- c0 (float): zero sequence capacitance, in nF
- len (float): length of the line, in km. This may be zero for a switch.
- phases (str): include A, B, and/or C if those phases are present in this link

The edata for each transformer link may contain:

- phs1 (str): include A, B, and/or C if those phases are present on the primary
- phs2 (str): include A, B, and/or C if those phases are present on the secondary
- conn1 (str): w if the primary is wye, d if delta
- conn2 (str): w if the secondary is wye, d if delta
- kv1 (float): primary winding kV rating, line-to-neutral for single-phase, line-to-line otherwise
- kv2 (float): secondary winding kV rating, line-to-neutral for single-phase, line-to-line otherwise
- kva1 (float): kva rating of the primary
- kva2 (float): kva rating of the secondary
- xhl (float): percent reactance
- r1 (float): equivalent positive sequence resistance, in Ohms from the primary
- x1 (float): equivalent positive sequence reactance, in Ohms from the primary
- r0 (float): equivalent zero sequence resistance, in Ohms from the primary
- x0 (float): equivalent zero sequence reactance, in Ohms from the primary
- phases (str): include A, B, and/or C if those phases are present in this link

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

lblDeltaY = 0.35

edgeTypes = {'line':            {'color':'gray',       'tag':'LN'},
             'transformer':     {'color':'orange',     'tag':'XFM'}}

nodeTypes = {'source':          {'color':'cyan',       'tag':'SUB', 'size':10, 'lblDeltaY': -lblDeltaY},
             'fault':           {'color':'red',        'tag':'FLT', 'size':10, 'lblDeltaY':  lblDeltaY},
             'der':             {'color':'gold',       'tag':'DER', 'size':25, 'lblDeltaY': -lblDeltaY},
             'capacitor':       {'color':'blue',       'tag':'CAP', 'size':15, 'lblDeltaY': -lblDeltaY},
             'recloser':        {'color':'green',    'tag':'REC', 'size':35, 'lblDeltaY': -lblDeltaY}}

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
        return 1.0
    if nph == 2:
        return 1.5
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

def parse_cv_casename (s):
    name = s[:-4]
    toks = name.split ('_')
    ckt = toks[0]
    loc = toks[1]
    phs = toks[2]
    if 'CAP' in loc:
        phs = 'ABC'
    return ckt, loc, phs

def parse_td_casename (s):
    name = s[6:]
    toks = name.split ('_')
    ckt = toks[0]
    loc = toks[1]
    phs = toks[2]
    if 'CAP' in loc:
        phs = 'ABC'
    return ckt, loc, phs

def format_relay_time (tval):
    tms = 1000.0 * float (tval)
    if tms < 0.0:
        tstr = '-'
    else:
        tstr = '{:.2f}'.format(tms)
    return tstr

def format_two_times (tphs, tgrnd):
    t1ms = 1000.0 * float (tphs)
    t2ms = 1000.0 * float (tgrnd)
    trip = t1ms
    if t2ms > 0.0:
        if (trip <= 0.0) or (t2ms < trip):
            trip = t2ms
    if trip <= 0.0:
        return '-'
    return '{:.2f}'.format(trip)

def read_relay_times (fname, myckt):
    aTimes = []
    with open(fname, mode='r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            ckt, loc, phs = parse_cv_casename (row[0])
            if (ckt == myckt) and (loc != 'CAP'):
                aTimes.append ({'Bus':loc, 'Phases':phs, 'Relay':row[1], 'T45':format_relay_time (row[3]), 
                    'Q46':format_relay_time (row[6]), 'Q47':format_relay_time (row[8])})
    return aTimes

def read_t400L_times (fname, myckt):
    aTimes = []
    with open(fname, mode='r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            ckt, loc, phs = parse_td_casename (row[0])
            if (ckt == myckt) and (loc != 'CAP'):
                aTimes.append ({'Bus':loc, 'Phases':phs, 'Relay':row[1], 'TF32':format_relay_time (row[3]), 
                    'OC21':format_two_times (row[4], row[5]), 'TD21':format_two_times (row[6], row[7])})
    return aTimes

def get_fault_label (n, relay, bus, phases, aTimes):
    if not aTimes:
        return ''
    for row in aTimes:
        if (row['Bus'] == bus) and (row['Phases'] == phases) and (row['Relay'] == relay):
            return '{:s}\nV45 {:s}\nQ46 {:s}\nQ47 {:s}'.format (n.upper(), row['T45'], row['Q46'], row['Q47'])
    return n.upper()

def get_t400L_label (n, relay, bus, phases, aTimes):
    if not aTimes:
        return ''
    for row in aTimes:
        if (row['Bus'] == bus) and (row['Phases'] == phases) and (row['Relay'] == relay):
            return '{:s}\nTF32 {:s}\nOC21 {:s}\nTD21 {:s}'.format (n.upper(), row['TF32'], row['OC21'], row['TD21'])
    return n.upper()

if __name__ == '__main__':
    print ('usage: python plot_opendss_feeder.py fdr_name nodes')
    print ('  fdr_name like ReducedNetwork')
    print ('  nodes is 1 to plot labels, 0 not to')
    feedername = 'ReducedNetwork'
    plotLabels = True
    if len(sys.argv) > 1:
        feedername = sys.argv[1]
        if len(sys.argv) > 2:
            if int(sys.argv[2]) > 0:
                plotLabels = True
            else:
                plotLabels = False

    lp = open (feedername + '.json').read()
    feeder = json.loads(lp)
    G = nx.readwrite.json_graph.node_link_graph(feeder)
    nbus = G.number_of_nodes()
    nbranch = G.number_of_edges()
    print ('read graph with', nbus, 'nodes and', nbranch, 'edges')

    # build a list of nodes, i.e., capacitors, DER and loads, that modify rendering
    cp = open ('PlotControl.json', 'r').read()
    config = json.loads(cp)
    for n, row in config['extranodes'].items():
        G.add_node (n.lower(), nclass=row['nclass'], ndata=row['ndata'])
    for cls in ['der', 'source', 'capacitor', 'fault', 'recloser']:
        for n in config[cls]:
            ng = n.lower()
            if ng in G.nodes():
                G.nodes()[ng]['nclass'] = cls
            else:
                print ('{:s} at {:s} not found'.format (cls, n))

    # find the relay operating times for this circuit
    aTimes = None
    sTimes = None
    if len(config['RelayTimeFile']) > 0:
        aTimes = read_relay_times (config['RelayTimeFile'], config['RelayCircuitName'])
    if len(config['T400LTimeFile']) > 0:
        sTimes = read_t400L_times (config['T400LTimeFile'], config['RelayCircuitName'])
#    for row in sTimes:
#        print (row)
#    quit()

    # extract the XY coordinates available for plotting
    xy = {}
    xyLbl = {}
    xyFlt = {}
    lblNode = {}
    lblFlt = {}
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
                    if nclass == 'fault':
#                        print (n, ndata)
#                        lblFlt[n] = get_fault_label (n, 'PVXFM', str(ndata['busnum']), 'A', aTimes)
#                        lblFlt[n] = get_t400L_label (n, 'PVXFM', str(ndata['busnum']), 'A', sTimes)
                        lblFlt[n] = get_fault_label (n, 'PVXF1', str(ndata['busnum']), 'ABC', aTimes)
#                        lblFlt[n] = get_t400L_label (n, 'PVXF1', str(ndata['busnum']), 'A', sTimes)
                        xyFlt[n] = [busx, busy + get_node_offset (nclass)]
                    else:
                        lblNode[n] = n.upper()
                        xyLbl[n] = [busx, busy + get_node_offset (nclass)]
                else:
                    nclass = 'other'
                plotNodes.append(n)
                nodeColors.append (get_node_color (nclass))
                nodeSizes.append (get_node_size (nclass))

    # extract the protection zones
    zones = {}  # keyed on the recloser buses
    target = config['source'][0].lower()
    for n in G.nodes():
        if 'nclass' in G.nodes()[n]:
            nclass = G.nodes()[n]['nclass']
            if nclass == 'recloser':
                zones[n] = []
    for n1,data in G.nodes(data=True):
        try:
            nodes = nx.shortest_path(G, n1, target)
            for n2 in nodes:
                if n2 in zones:
                    zones[n2].append (n1)
                    break
#            print (n1, nodes)
        except:
            pass
    for key, val in zones.items():
        print ('Zone Start Bus {:s}; {:d} OpenDSS Buses; {:s}'.format (key, len(val), ','.join(val)))
    busmap = {}
    mp = open(feedername + '.atpmap','r')
    for row in mp:
        busname, busnum, phases = row.lower().split()
        if busname not in busmap:
            busmap[busname] = int(busnum)
    mp.close()
    for key, val in zones.items():
        print ('Zone Start Bus {:d}; {:d} ATP Buses; {:s}'.format (busmap[key], len(val), 
            ','.join([str(busmap[x]) for x in val])))

#    quit()

    # only plot the edges that have XY coordinates at both ends
    plotEdges = []
    edgeWidths = []
    edgeColors = []
    for n1, n2, data in G.edges(data=True):
        bFound = False
        if n1 in xy:
            if n2 in xy:
                bFound = True
                nph = len(data['edata']['phases'])
                plotEdges.append ((n1, n2))
                edgeWidths.append (get_edge_width(nph))
                edgeColors.append (get_edge_color(data['eclass']))
        if not bFound:
            print ('unable to plot', data['ename'])

    fig, ax = plt.subplots()
    nx.draw_networkx_nodes (G, xy, nodelist=plotNodes, node_color=nodeColors, node_size=nodeSizes, ax=ax)
    nx.draw_networkx_edges (G, xy, edgelist=plotEdges, edge_color=edgeColors, width=edgeWidths, alpha=0.8, ax=ax)
    if plotLabels:
        nx.draw_networkx_labels (G, xyLbl, lblNode, font_size=8, font_color='k', 
                                 horizontalalignment='left', verticalalignment='baseline', ax=ax)
        nx.draw_networkx_labels (G, xyFlt, lblFlt, font_size=8, font_color='r', 
                                 horizontalalignment='left', verticalalignment='bottom', ax=ax)
    plt.title (config['PlotTitle'])
    plt.xlabel ('X coordinate [k]')
    plt.ylabel ('Y coordinate [k]')
    plt.grid(linestyle='dotted')
    xdata = [0, 1]
    ydata = [1, 0]
    lns = [lines.Line2D(xdata, ydata, color=get_edge_color(e)) for e in edgeTypes] + \
        [lines.Line2D(xdata, ydata, color=get_node_color(n), marker='o') for n in nodeTypes]
    labs = [get_edge_mnemonic (e) for e in edgeTypes] + [get_node_mnemonic (n) for n in nodeTypes]
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    plt.legend(lns, labs, loc='lower right')
    plt.savefig ('j1reduced.pdf')
    plt.show()

