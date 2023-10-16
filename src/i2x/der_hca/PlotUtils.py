import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from .hca import HCA, print_config
from io import StringIO
import networkx as nx
import i2x.api as i2x

def get_sequence(vabc):

    a = np.exp(1j*np.pi*2/3)
    Ainv = (1/3)* np.array([[1, 1, 1], [1, a, np.power(a,2)], [1, np.power(a,2), a ]])

    return Ainv.dot(vabc.transpose()).transpose()
    
def lower(x):
    if isinstance(x, str):
        return x.lower()
    else:
        return x
    
def upper(x):
    if isinstance(x, str):
        return x.upper()
    else:
        return x

def str_in(s, v):
    """check whether s is in v.
    consider s.lower() and s.upper()
    """
    for k in [s, lower(s), upper(s)]:
        if k in v:
            return True, k
    return False, s

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


def inverter_control_plot(choice, filename=None, **kwargs):
    row = i2x.inverterChoices[choice]
    fig = make_subplots(2,1, shared_xaxes=True, subplot_titles=("reactive power", "active power"))
    colors = ColorList()
    add_trace(fig, row["v"], row["q"], "Q", colors=colors, row=1, col=1)
    colors.step()
    add_trace(fig, row["v"], row["p"], "P", colors=colors, row=2, col=1)
    fig.update_xaxes(title_text="V [p.u.]", row=2)
    fig.update_yaxes(title_text="Q [p.u.]", row=1)
    fig.update_yaxes(title_text="P [p.u.]", row=2)
    if filename is None:
        fig.show()
    else:
        fig.write_html(f"{filename}.html", **kwargs)


def vdiff_plot(hcaobj:HCA, filenamebase, typ="pv", **kwargs):
    """plot voltage difference issue on feeder.
    IMPORTANT: anything passed to **kwargs goes to the write_html plotly call
    for BOTH the time plots as well as the feeder plot.
    """
    vdiff_locations = hcaobj.metrics.get_vdiff_locations()
    if len(vdiff_locations["v"]) == 0:
        print("No locations violating the voltage difference metric. Exiting.")
        return
    fig = make_subplots(2, 1, shared_xaxes=True, subplot_titles=("node voltage", "node voltage diff"))
    colors = ColorList()
    highlight_nodes={}
    for node in vdiff_locations["v"].keys():
        x2 = list(range(len(vdiff_locations["vdiff"][node])))
        x1 = list(range(len(vdiff_locations["v"][node])))
        add_trace(fig, x1, vdiff_locations["v"][node], f"{node}_v", colors=colors, row=1)
        add_trace(fig, x2, vdiff_locations["vdiff"][node], f"{node}_dv", colors=colors, row=2)
        colors.step()
        highlight_nodes[node] = f"<br>max vdiff: {np.max(np.abs(vdiff_locations['vdiff'][node])):0.2f} %"
    fig.add_hline(y=hcaobj.metrics.lims["voltage"]["vdiff"], row=2, line_dash="dash")
    fig.update_yaxes(title_text="V [p.u.]", row=1, col=1)
    fig.update_yaxes(title_text="dV [%]", row=2, col=1)
    fig.write_html(f"{filenamebase}.html", **kwargs)
    ## plot feeder
    feeder_plotter = PlotlyFeeder()
    feeder_plotter.plot(hcaobj.G, f"{filenamebase}_feeder.html",
                        highlight_nodes=highlight_nodes,
                        extra_node_text=hc_text(hcaobj, typ), 
                        extra_edge_text=upgrade_text(hcaobj), **kwargs)

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


def thermal_plot(hcaobj:HCA, filenamebase, typ="pv", **kwargs):
    # branches = []
    # for v in hcaobj.metrics.get_thermal_branches().values():
    #     branches.extend(v)
    branches = {}
    for k, v in hcaobj.metrics.get_thermal_branches().items():
        for br in v:
            branches[br] = f"Thermal violation: {hcaobj.metrics.violation['thermal']['emerg'][f'{k}.{br}']:0.3f} %"
    ## plot feeder
    feeder_plotter = PlotlyFeeder()
    feeder_plotter.plot(hcaobj.G, f"{filenamebase}.html",
                        extra_node_text=hc_text(hcaobj, typ), 
                        highlight_edges=branches,
                        include_plotlyjs='cdn', **kwargs)


def island_plots(hcaobj:HCA, filenamebase, plot_feeder=False, **kwargs):
    """Plot the aggregate flow in/out of all components"""
    fig = make_subplots(2, 1, shared_xaxes=True, subplot_titles=("Net P Flow [kW] (pos->exporting)", "Net Q Flow [kVAr] (pos->exporting"))
    colors = ColorList()
    for comp, vals in hcaobj.lastres["compflows"].items():
        p = vals["p"].sum(axis=1)
        q = vals["q"].sum(axis=1)
        x = list(range(len(p)))
        add_trace(fig, x, p, f"comp {comp}: P", colors=colors, row=1)
        add_trace(fig, x, q, f"comp {comp}: Q", colors=colors, row=2)
        colors.step()
    fig.update_yaxes(title_text="P [kW]", row=1, col=1)
    fig.update_yaxes(title_text="Q [kVAr]", row=2, col=1)
    fig.write_html(f"{filenamebase}.html", **kwargs)
    if plot_feeder:
        feeder_plotter = PlotlyFeeder()
        feeder_plotter.plot(hcaobj.G, f"{filenamebase}_feeder.html",
                            comp_plot=True, **kwargs)

#TODO possibly an option to show components and aggregate for a single component

def hc_plot(hcaobj:HCA, filenamebase, typ="pv", **kwargs):
    feeder_plotter = PlotlyFeeder()
    feeder_plotter.plot(hcaobj.G, f"{filenamebase}.html",
                        extra_node_text=hc_text(hcaobj, typ),
                        extra_edge_text=upgrade_text(hcaobj),
                        include_plotlyjs='cdn', **kwargs)

def upgrade_plot(hcaobj:HCA, filenamebase, typ="pv", **kwargs):
    feeder_plotter = PlotlyFeeder()
    feeder_plotter.plot(hcaobj.G, f"{filenamebase}.html",
                        extra_node_text=hc_text(hcaobj, typ),
                        highlight_edges=upgrade_text(hcaobj),
                        **kwargs)

def hc_text(hcaobj:HCA, typ):
    out = {}
    # for n in hcaobj.visited_buses:
    for n, hc in hcaobj.get_data("hc", typ).to_dict("index").items():
        # hc, cnt = hcaobj.get_hc(typ, n)
        cnt = hc.pop("cnt")
        out[n] = dict2str(hc, f"HC | {typ} | round {cnt}", newline="<br>")
    return out

def upgrade_text(hcaobj:HCA):
    out = {}
    for typ, vals in hcaobj.data["upgrades"].items():
        for br, v in vals.items():
            out[br] = dict2str(v, f"Upgrades", newline="<br>")
    return out

def dict2str(d, n, newline='\n'):
    ftmp = StringIO()
    def strprint(s):
        print(s, file=ftmp)
    print_config(d, printf=strprint, title=n)
    s = ftmp.getvalue()
    if newline != '\n':
        s = s.replace("\n", "<br>")
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
        "load":       {'color': 'brown', 'tag':"LD", 'size': 7, "symbol": "triangle-down"},
        "highlight":  {'color': 'yellow', 'tag': "HIL", 'size': 16, "symbol": "star"}
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
        'fuse':        {'color':'magenta','tag':'FUS'},
        "highlight":   {'color': 'yellow', 'tag': "HIL"}
        }

        self.node_x = {}
        self.node_y = {}
        self.node_txt = {}
        self.node_size = {}
        self.plotnodes = {}

        self.edge_x = {}
        self.edge_y = {}
        self.edge_txt = {}
        # see https://stackoverflow.com/questions/46037897/line-hover-text-in-plotly
        self.midnode_x = {}
        self.midnode_y = {}

        self.colors = ColorList()

    def get_node_mnemonic(self, nclass):
        if nclass in self.nodeTypes:
            return self.nodeTypes[nclass]['tag']
        else:
            return nclass
    
    def get_node_symbol(self, nclass):
        if nclass in self.nodeTypes:
            return self.nodeTypes[nclass]["symbol"]
        else:
            return "circle"

    def get_node_size(self, nclass, altclass=None):
        if altclass is None:
            if nclass in self.nodeTypes:
                return self.nodeTypes[nclass]['size']
        else:
            if altclass in self.nodeTypes:
                return self.nodeTypes[altclass]['size']
        return 5

    def get_node_color(self, nclass):
        if nclass in self.nodeTypes:
            return self.nodeTypes[nclass]['color']
        elif "comp" in nclass:
            self.colors.setidx(int(nclass.split("comp")[1]))
            return self.colors()
        return 'black'
    
    def get_edge_mnemonic(self, eclass):
        if eclass in self.edgeTypes:
            return self.edgeTypes[eclass]['tag']
        else:
            return eclass

    def get_edge_color(self, eclass):
        if eclass in self.edgeTypes:
            return self.edgeTypes[eclass]['color']
        elif "comp" in eclass:
            self.colors.setidx(int(eclass.split("comp")[1]))
            return self.colors()
    
    def clear_node_data(self):
        self.node_x = {}
        self.node_y = {}
        self.node_txt = {}
        self.node_size = {}
        self.plotnodes = {}

    def collect_node_data(self, G:nx.Graph, comp_plot=False, highlight_nodes=dict(), extra_text=dict()):
        self.clear_node_data()
        for n, d in G.nodes(data=True):
            try:
                ndata = d["ndata"]
            except KeyError:
                continue
            if "x" in ndata:
                highlight_test, highlight_key = str_in(n, highlight_nodes.keys())
                altclass = None
                if highlight_test:
                    nclass = "highlight"
                    text_extra = "<br>" + highlight_nodes[highlight_key]
                    extra_test, extra_key = str_in(n, extra_text.keys())
                    if extra_test:
                        text_extra += "<br>"+ extra_text[extra_key]
                else:
                    if comp_plot:
                        nclass = f'comp{d["comp"]}'
                        altclass = d["nclass"]
                    else:
                        nclass = d["nclass"]
                    extra_test, extra_key = str_in(n, extra_text.keys())
                    if extra_test:
                        text_extra = "<br>" + extra_text[extra_key]
                    else:
                        text_extra = ""
                if not nclass in self.node_x:
                    self.node_x[nclass] = []
                    self.node_y[nclass] = []
                    self.node_txt[nclass] = []
                    self.node_size[nclass] = []
                self.plotnodes[n] = (float(ndata["x"]) / 1000.0, float(ndata["y"]) / 1000.0)
                self.node_x[nclass].append(float(ndata["x"]) / 1000.0)
                self.node_y[nclass].append(float(ndata["y"]) / 1000.0)
                self.node_txt[nclass].append(dict2str(d, n).replace("\n", "<br>") + text_extra)
                self.node_size[nclass].append(self.get_node_size(nclass, altclass=altclass))

    def clear_edge_data(self):
        self.edge_x = {}
        self.edge_y = {}
        self.edge_txt = {}
        self.midnode_x = {}
        self.midnode_y = {}
    
    def collect_edge_data(self, G:nx.Graph, comp_plot=False, highlight_edges=dict(), extra_text=dict()):
        self.clear_edge_data()
        for u,v,d in G.edges(data=True):
            if not ((u in self.plotnodes) and (v in self.plotnodes)):
                # only plot edges where both ends have coordinates
                continue
            highlight_test, highlight_key = str_in(d["ename"], highlight_edges.keys())
            if highlight_test:
                eclass = "highlight"
                text_extra = "<br>" + highlight_edges[highlight_key]
                extra_test, extra_key = str_in(d["ename"], extra_text.keys())
                if extra_test:
                    text_extra += "<br>" + extra_text[extra_key]
            else:
                if comp_plot and (G.nodes[u]["comp"] == G.nodes[v]["comp"]):
                    eclass = f'comp{G.nodes[u]["comp"]}'
                else:
                    eclass = d["eclass"]
                extra_test, extra_key = str_in(d["ename"], extra_text.keys())
                if extra_test:
                    text_extra = "<br>" + extra_text[extra_key]
                else:
                    text_extra = ""
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
            self.edge_txt[eclass].append(dict2str(d, d["ename"]).replace("\n", "<br>") + text_extra)

    
    def make_plot(self, filename, title=None, **kwargs):
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
        if title is not None:
            fig.update_layout(title=title)
        fig.write_html(filename, **kwargs)

    def plot(self, G, filename, comp_plot=False,
             highlight_nodes=dict(), highlight_edges=dict(), 
             extra_node_text=dict(), extra_edge_text=dict(),
             **kwargs):
        self.collect_node_data(G, comp_plot=comp_plot, highlight_nodes=highlight_nodes, extra_text=extra_node_text)
        self.collect_edge_data(G, comp_plot=comp_plot, highlight_edges=highlight_edges, extra_text=extra_edge_text)
        self.make_plot(filename, **kwargs)