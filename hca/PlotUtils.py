import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from hca import HCA

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
    