import networkx as nx

def trace_pcc_path(G, source, target):
  if G.is_directed():
    U = G.to_undirected()
  else:
    U = G
  d = {'loadkw':0.0, 'genkva':0.0, 'pvkva':0.0, 'batkva':0.0, 'capkvar':0.0, 'length':0.0,
  'reclosers':[], 'transformers':[], 'regulators':[], 'switches':[], 'fuses':[]}

  nodes = nx.shortest_path(U, source, target)
  edges = zip(nodes[0:], nodes[1:])
  for n in nodes:
    nclass = U.nodes()[n]['nclass']
    ndata = U.nodes()[n]['ndata']
    for tag in ['loadkw', 'genkva', 'pvkva', 'batkva', 'capkvar']:
      if tag in ndata:
        d[tag] += ndata[tag]
  for u, v in edges:
    eclass = U[u][v]['eclass']
    ename = U[u][v]['ename']
    edata = U[u][v]['edata']
    if 'length' in edata:
      d['length'] += edata['length']
    if eclass == 'recloser':
      d['reclosers'].append(ename)
    elif eclass == 'transformer':
      d['transformers'].append(ename)
    elif eclass == 'regulator':
      d['regulators'].append(ename)
    elif eclass == 'fuse':
      d['fuses'].append(ename)
    elif eclass == 'switch':
      d['switches'].append(ename)
  return d
