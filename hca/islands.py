import networkx as nx
from typing import Tuple
from i2x.plot_opendss_feeder import load_opendss_graph, plot_opendss_feeder
import pandas as pd
import copy
import numpy as np
import matplotlib.pyplot as plt 
import itertools

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

def check_radial(G: nx.classes.graph.Graph) -> bool:
    """
    Check whether G is radial
    """

    H = G.copy()
    ## get the open switches and remove them from the graph
    open_switches = get_branch_elem(H, ['eclass', 'SwtOpen'], ['swtcontrol', True])
    H.remove_edges_from(open_switches)

    return nx.is_tree(H)

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
    add_comp_num(G, comps) # add component numbers to original graph
    return comps, reclosers, comp2recloser(comps, reclosers, G)

def add_branch_weights(G: nx.classes.graph.Graph):
    """
    Add a "weight" property to each edge:
        - 1 for each edge that is "closed"
        - G.number_of_edges() for any open edge
    """
    
    # get open switches
    open_switches = get_branch_elem(G, ['eclass', 'SwtOpen'], ['swtcontrol', True])
    open_weight = G.number_of_edges()

    G.add_edges_from(G.edges(data=True), weight=1)
    G.add_edges_from(open_switches, weight=open_weight)

def add_comp_num(G: nx.classes.graph.Graph, comps:list):
    for i, c in enumerate(comps):
        nx.set_node_attributes(G, {n: {"comp": i} for n in c})

def get_sources(G):
    return [n for n, d in G.nodes(data=True) if d["nclass"] == "source"]

def get_comps(e:tuple, comps:list) -> tuple:
    """ 
    Get a tuple of (from component, to component) for link element e
    out of the list of components, comps
    """
    return ([e[0] in c for c in comps].index(True), [e[1] in c for c in comps].index(True))

def map_reclosers(comps:list, reclosers:list) -> dict:
    """
    return a dictionary keyed on the recloser tuple with values indicating which two
    components it connects
    """
    
    return {e[0:2]: get_comps(e, comps) for e in reclosers}


def get_components_reclosers(compid, recloser_map):
    """
    Return all the reclosers that touch component id compid
    """
    return [k for k, v in recloser_map.items() if compid in v]

def get_recloser_dir(e:tuple, G: nx.classes.graph.Graph, sources = None):
    """
    Check whether the recloser
    Inputs:
        e: tuple (from_bus, to_bus)
        sources: list of feeder sources
    """
    if sources is None:
        sources = get_sources(G)
    direction = []
    for s in sources:
        # get path from from node to source
        try:
            p = nx.shortest_path(G, e[0], s)
            if p[1] == e[1]:
                # positive direction is going through element to source
                direction.append(1)
            else:
                # negative direction is going through element to source
                direction.append(-1)
        except nx.NetworkXNoPath:
            # no path found
            direction.append(None)
    
    out = np.unique([i for i in direction if i is not None])
    if len(out) == 1:
        return out[0]
    else:
        raise ValueError(f"Recloser cannot be determined: sources = {sources}, directions = {direction}")
    

def comp2recloser(comps:list, reclosers:list, G: nx.classes.graph.Graph) -> dict:
    """
    Return a dictionary of compid -> list of reclosers (tuple)
    """
    # sources = get_sources(G)
    out = {i: [] for i in range(len(comps))}
    for e in reclosers:
        # direction = get_recloser_dir((e[2]['edata']['bus1'], e[2]['edata']['bus2']), G, sources=sources)
        # c1, c2 = get_comps(e, comps)
        c1, c2 = get_comps((e[2]['edata']['bus1'], e[2]['edata']['bus2']), comps)
        out[c1].append(copy.deepcopy(e))
        out[c1][-1][2]["direction"] = 1 # positive means flow *out* of component
        out[c2].append(copy.deepcopy(e))
        out[c2][-1][2]["direction"] = -1 # positive means flow *out* of component
    return out


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

def plot_components(n, m, G, comps):
    fig, ax = plt.subplots(n,m, figsize=(16,9))
    for i, idx in enumerate(itertools.product(range(n),range(m))):
        if i == len(comps):
            break
        show_component(G, comps, i, plot=True, fig=fig, ax=ax[idx], on_canvas=True)
        ax[idx].get_legend().remove()
    plt.show()
    

def island_flows(compid:int, comp2rec:dict, recdict:dict):
    """
    Collect active and reactive power flowing in/out of
    component `compid`
    """
    df = {"p": {}, "q": {}}
    for e in comp2rec[compid]:
        name = e[2]["ename"]
        direction = e[2]["direction"]
        df["p"][name] = direction * recdict[name]["p"]
        df["q"][name] = direction * recdict[name]["q"]
    df = {k: pd.DataFrame(v) for k, v in df.items()}
    df["lims"] = pd.DataFrame({k: df[k].sum(axis=1).agg(["min", "max", minabs]).to_dict() for k in ["p", "q"]})

    return df

def all_island_flows(comp2rec:dict, recdict:dict):
    return {i: island_flows(i, comp2rec, recdict) for i in comp2rec.keys()}    

def minabs(x):
    return x.abs().min()