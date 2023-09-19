import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from hca import HCA
import hca as h
from io import StringIO
import networkx as nx

def get_sequence(vabc):

    a = np.exp(1j*np.pi*2/3)
    Ainv = (1/3)* np.array([[1, 1, 1], [1, a, np.power(a,2)], [1, np.power(a,2), a ]])

    return Ainv.dot(vabc.transpose()).transpose()

def get_pout_primary(droop, f, pref, f0=60):
    """
    return the power output due to the current frequency, power reference
    and droop setting.
    pref should be in p.u.
    -droop * dP = (f - f0)/f0
    where dP = p - pref

    dP = -(1/droop)* (f - f0)/f0
    p = pref - (1/droop) * (f - f0)/f0
    """
    if droop == 0:
        return pref
    else:
        return pref - (1/droop) * (f - f0)/f0
    

class ColorList:
    def __init__(self):
        self.cidx = 0
        self.colors = px.colors.qualitative.Plotly
        self.n = len(self.colors)
    def __call__(self):
        return self.colors[self.cidx]
    def step(self):
        self.cidx = (self.cidx + 1) % self.n
    def setidx(self, cidx):
        self.cidx = cidx
    def getidx(self):
        return self.cidx
    def shiftidx(self, shift):
        self.cidx = (self.cidx + shift) % self.n

def plot_blank(fig, x=[0], y=[0], row=1, col=1, **kwargs):
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line_color="white", name="", visible='legendonly', **kwargs), row=row, col=col)

def add_trace(fig, x, y, name, total_sec=True, colors=None, row=1, col=1, **kwargs):
    if colors is None:
        colors = ColorList()
    
    if (total_sec and (isinstance(x, pd.DataFrame) or isinstance(x, pd.Series))):
        x = (x.index-x.index[0]).total_seconds()

    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=name, line_color=colors(), **kwargs), 
                row=row, col=col)

def vdiff_plot(hcaobj:HCA, filenamebase):
    vdiff_locations = hcaobj.metrics.get_vdiff_locations()
    fig = make_subplots(2, 1, shared_xaxes=True, subplot_titles=("node voltage", "node voltage diff"))
    colors = ColorList()
    for node in vdiff_locations["v"].keys():
        x2 = list(range(len(vdiff_locations["vdiff"][node])))
        x1 = list(range(len(vdiff_locations["v"][node])))
        add_trace(fig, x1, vdiff_locations["v"][node], f"{node}_v", colors=colors, row=1)
        add_trace(fig, x2, vdiff_locations["vdiff"][node], f"{node}_dv", colors=colors, row=2)
        colors.step()
    fig.add_hline(y=hcaobj.metrics.lims["voltage"]["vdiff"], row=2, line_dash="dash")
    fig.update_yaxes(title_text="V [p.u.]", row=1, col=1)
    fig.update_yaxes(title_text="dV [%]", row=2, col=1)
    fig.write_html(f"{filenamebase}.html")
    hcaobj.plot(highlight_nodes=list(vdiff_locations["v"].keys()), pdf_name=f"{filenamebase}.pdf", on_canvas=True)

def vmaxmin_plot(hcaobj:HCA, filenamebase):
    vmaxlocs = hcaobj.metrics.get_volt_max_buses()
    vminlocs = hcaobj.metrics.get_volt_min_buses()

    lims = hcaobj.metrics.base.volt_stats.loc[:, "limits"]
    
    fig = make_subplots(2, 1, shared_xaxes=True, subplot_titles=("vmax violations", "vmin violations"))
    colors = ColorList()
    for node, v in vmaxlocs.items():
        x = list(range(len(v)))
        add_trace(fig, x, v, f"{node}_vmax", colors=colors, row=1)
        colors.step()
    for i in ["MaxVoltage", "MaxLVVoltage"]:
        fig.add_hline(y=lims[i], line_dash="dash", row=1, annotation_text=i)

    for node, v in vminlocs.items():
        x = list(range(len(v)))
        add_trace(fig, x, v, f"{node}_vmin", colors=colors, row=2)
        colors.step()
    for i in ["MinVoltage", "MinLVVoltage"]:
        fig.add_hline(y=lims[i], line_dash="dash", row=2, annotation_text=i)
    
    for i in [1,2]:
        fig.update_yaxes(title_text="V [p.u.]", row=i, col=1)
    fig.write_html(f"{filenamebase}.html")
    hcaobj.plot(highlight_nodes=list(vmaxlocs.keys()) + list(vminlocs.keys()), pdf_name=f"{filenamebase}.pdf", on_canvas=True)


def thermal_plot(hcaobj:HCA, filenamebase):
    branches = []
    for v in hcaobj.metrics.get_thermal_branches().values():
        branches.extend(v)
    hcaobj.plot(highlight_edges=branches, pdf_name=f"{filenamebase}.pdf", on_canvas=True)


def dict2str(d, n):
    ftmp = StringIO()
    def strprint(s):
        print(s, file=ftmp)
    h.print_config(d, printf=strprint, title=n)
    s = ftmp.getvalue()
    ftmp.close()
    return s

class PlotlyFeeder:
    def __init__(self):
        self.nodeTypes = {
        'source':     {'color':'cyan',   'tag':'SUB', 'size':14, "symbol": "square"},
        'generator':  {'color':'red',    'tag':'GEN', 'size':14, "symbol": "circle"},
        'solar':      {'color':'gold',   'tag':'PV',  'size':14, "symbol": "star-square"},
        'capacitor':  {'color':'blue',   'tag':'CAP', 'size':12, "symbol": "circle"},
        'storage':    {'color':'green',  'tag':'BAT', 'size':14, "symbol": "pentagon"},
        "bus":        {'color': 'black', 'tag':"BUS", 'size':5, "symbol": "circle"},
        "load":       {'color': 'brown', 'tag':"LD", 'size': 7, "symbol": "triangle-down"}
        }

        self.edgeTypes = {
        'line':        {'color':'gray',   'tag':'LN'},
        'transformer': {'color':'orange', 'tag':'XFM'},
        'regulator':   {'color':'red',    'tag':'REG'},
        'switch':      {'color':'cornflowerblue',   'tag':'SWT'},
        'swtcontrol':  {'color':'blue',   'tag':'CTL'},
        'nwp':         {'color':'magenta','tag':'NWP'},
        'recloser':    {'color':'lime',   'tag':'REC'},
        'reactor':     {'color':'green',  'tag':'RCT'},
        'fuse':        {'color':'magenta','tag':'FUS'}
        }

        self.node_x = {}
        self.node_y = {}
        self.node_txt = {}
        self.node_size = {}
        self.plotnodes = {}

        edge_x = {}
        edge_y = {}
        edge_txt = {}
        # see https://stackoverflow.com/questions/46037897/line-hover-text-in-plotly
        midnode_x = {}
        midnode_y = {}

    def get_node_mnemonic(self, nclass):
        return self.nodeTypes[nclass]['tag']
    
    def get_node_symbol(self, nclass):
        return self.nodeTypes[nclass]["symbol"]

    def get_node_size(self, nclass, highlight=False):
        if highlight:
            return 35
        if nclass in self.nodeTypes:
            return self.nodeTypes[nclass]['size']
        return 5

    def get_node_color(self, nclass, highlight=False):
        if nclass in self.nodeTypes:
            if highlight:
                return "yellow"
            else:
                return self.nodeTypes[nclass]['color']
        return "yellow" if highlight else 'black'
    
    def get_edge_mnemonic(self, eclass):
        return self.edgeTypes[eclass]['tag']

    def get_edge_color(self, eclass, highlight=False):
        if highlight:
            return "yellow"
        else:
            return self.edgeTypes[eclass]['color']
    
    def clear_node_data(self):
        self.node_x = {}
        self.node_y = {}
        self.node_txt = {}
        self.node_size = {}
        self.plotnodes = {}

    def collect_node_data(self, G:nx.Graph):
        self.clear_node_data()
        for n, d in G.nodes(data=True):
            try:
                ndata = d["ndata"]
            except KeyError:
                continue
            if "x" in ndata:
                nclass = d["nclass"]
                if not nclass in self.node_x:
                    self.node_x[nclass] = []
                    self.node_y[nclass] = []
                    self.node_txt[nclass] = []
                    self.node_size[nclass] = []
                self.plotnodes[n] = (float(ndata["x"]) / 1000.0, float(ndata["y"]) / 1000.0)
                self.node_x[nclass].append(float(ndata["x"]) / 1000.0)
                self.node_y[nclass].append(float(ndata["y"]) / 1000.0)
                self.node_txt[nclass].append(dict2str(d, n).replace("\n", "<br>"))
                self.node_size[nclass].append(self.get_node_size(nclass))

    def clear_edge_data(self):
        self.edge_x = {}
        self.edge_y = {}
        self.edge_txt = {}
        self.midnode_x = {}
        self.midnode_y = {}
    
    def collect_edge_data(self, G:nx.Graph):
        self.clear_edge_data()
        for u,v,d in G.edges(data=True):
            if not ((u in self.plotnodes) and (v in self.plotnodes)):
                # only plot edges where both ends have coordinates
                continue
            eclass = d["eclass"]
            if not eclass in self.edge_x:
                self.edge_x[eclass] = []
                self.edge_y[eclass] = []
                self.edge_txt[eclass] = []
                self.midnode_x[eclass] = []
                self.midnode_y[eclass] = []
            self.edge_x[eclass] += [self.plotnodes[u][0], self.plotnodes[v][0], None]
            self.edge_y[eclass] += [self.plotnodes[u][1], self.plotnodes[v][1], None]
            self.midnode_x[eclass].append((self.plotnodes[u][0] + self.plotnodes[v][0])/2)
            self.midnode_y[eclass].append((self.plotnodes[u][1] + self.plotnodes[v][1])/2)
            self.edge_txt[eclass].append(dict2str(d, d["ename"]).replace("\n", "<br>"))

    
    def make_plot(self, filename, **kwargs):
        node_traces = {}
        for nclass in self.node_x.keys():
            node_traces[nclass] = go.Scatter(
                x = self.node_x[nclass], y = self.node_y[nclass],
                mode='markers',
                hoverinfo='text',
                text=self.node_txt[nclass],
                name=self.get_node_mnemonic(nclass),
                marker_color= self.get_node_color(nclass),
                marker_symbol=self.get_node_symbol(nclass),
                marker=dict(size=self.node_size[nclass])
            )
        edge_traces = {}
        midnode_traces = {}
        for eclass in self.edge_x.keys():
            edge_traces[eclass] = go.Scatter(
                x = self.edge_x[eclass], y = self.edge_y[eclass],
                mode='lines',
                hoverinfo='none',
                line_color = self.get_edge_color(eclass),
                name = self.get_edge_mnemonic(eclass)
            )
            midnode_traces[eclass] = go.Scatter(
                x = self.midnode_x[eclass], y= self.midnode_y[eclass],
                text = self.edge_txt[eclass],
                mode='markers',
                hoverinfo='text',
                opacity=0,
                marker_color= self.get_edge_color(eclass),
                showlegend=False
            )
        fig = go.Figure()
        for nclass, ntrace in node_traces.items():
            fig.add_trace(ntrace)
        for eclass, etrace in edge_traces.items():
            fig.add_trace(etrace)
            fig.add_trace(midnode_traces[eclass])

        fig.write_html(filename, **kwargs)

    def plot(self, G, filename, **kwargs):
        self.collect_node_data(G)
        self.collect_edge_data(G)
        self.make_plot(filename, **kwargs)