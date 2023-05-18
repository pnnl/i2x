import networkx as nx
from typing import Tuple
from i2x.plot_opendss_feeder import load_opendss_graph, plot_opendss_feeder

def get_branch_elem(G:nx.classes.graph.Graph, keys:list, vals:list) -> list:
    """
    Get all branches of graph G that have eclass = elem.
    Returns a list of the edges: tuples (u,v,d)
    """

    if len(keys) != len(vals):
        raise ValueError("Length of keys and vals must be equal!")
    ebunch = []
    for (u,v,d) in G.edges(data=True):
        test = True
        for key,val in zip(keys,vals):
            try:
                if d[key] == val:
                    continue
                else:
                    test = False
                    break
            except KeyError:
                if d['edata'][key] == val:
                    continue
                else:
                    test = False
                    break
        if test:
            ebunch.append((u,v,d))
    return ebunch


def get_islands(G: nx.classes.graph.Graph) -> Tuple[list, list]:
    """
    Get the components of graph G that can be islanded via reclosers.
    Returns a list of components. A subgraph can then be created with
    G.subgraph(comps[i]) for a desired i.
    The components are sorted from largest to smallest.
    """

    H = G.copy() # so we don't mess the original graph

    ## get the open switches and remove them from the graph
    open_switches = get_branch_elem(H, ['eclass', 'SwtOpen'], ['swtcontrol', True])
    H.remove_edges_from(open_switches)

    ## get the reclosers and remove them from graph to create islands
    reclosers = get_branch_elem(H, ['eclass'], ['recloser'])
    H.remove_edges_from(reclosers)

    comps = sorted(nx.connected_components(H), key=len, reverse=True)

    return comps, reclosers

def get_comps(e:tuple, comps:list) -> tuple:
    """ 
    Get a tuple of (from component, to component) for link element e
    out of the list of components, comps
    """
    return ([e[0] in c for c in comps].index(True), [e[1] in c for c in comps].index(True))

def show_component(G, comps, i, printvals=True, printheader=False, printfun=print, plot=False, **kwargs):
    cap = {k: 0 for k in ["loadkw", "genkw", "pvkw", "batkw"]}
    for n, d  in G.subgraph(comps[i]).nodes(data=True):
        for k in cap:
            cap[k] += d["ndata"][k]
    
    if printvals:
        if printheader:
            printfun("comp       nodes   loadkw   genkw     pvkw    batkw  ")
            printfun("-------- -------- -------- -------- -------- --------")
        printfun(f'comp {i:3d} {len(comps[i]):8d} {cap["loadkw"]:8.2f} {cap["genkw"]:8.2f} {cap["pvkw"]:8.2f} {cap["batkw"]:8.2f}')

    if plot:
        plot_opendss_feeder(G.subgraph(comps[i]), **kwargs)