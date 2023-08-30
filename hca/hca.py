import i2x.api as i2x
import random
import math
import networkx as nx
import argparse
import json
import sys
import islands as isl
import numpy as np
import py_dss_interface
from hca_utils import Logger, merge_configs
import os
import pandas as pd
import copy
import hashlib


SQRT3 = math.sqrt(3.0)

def print_config(config:dict, tabs="", printf=print):
    """print a configuration dictionary"""
    if not tabs:
      printf("\n===================================\nConfiguration:\n===================================")
    for k, v in config.items():
        if isinstance(v, dict):
            printf(f"{tabs}{k}:")
            print_config(v, tabs=tabs+"\t", printf=printf)
        else:
            printf(f"{tabs}{k}:{v}")

def print_column_keys (label, d):
  columns = ''
  for key, row in d.items():
    columns = 'described by ' + str(row.keys())
    break
  print ('{:4d} {:20s} {:s}'.format (len(d), label, columns))

def activate_monitor_byname(dss:py_dss_interface.DSSDLL, monitorname:str) -> int:
  """
  activate monitor, return 0 if monitor not found
  """

  idx = dss.monitors.first()
  while idx > 0:
    if monitorname == dss.monitors.name:
      return idx
    idx = dss.monitors.next()
  return idx
  

def activate_monitor_byelem(dss:py_dss_interface.DSSDLL, elemname:str, mode:int) -> int:
  """
  activate monitor, return 0 if monitor not found
  """

  idx = dss.monitors.first()
  while idx > 0:
    if (elemname == dss.monitors.element) and (mode == dss.monitors.mode):
      return idx
    idx = dss.monitors.next()
  return idx

def activate_xfrm_byname(dss:py_dss_interface.DSSDLL, xfrm):
  """
  activate transformer in the dss object
  """

  idx = dss.transformers.first()
  while idx > 0:
    if dss.transformers.name == xfrm:
      return idx
    idx = dss.transformers.next()
  return idx

def get_parallel_xfrm(dss:py_dss_interface.DSSDLL,xfrm):
  """
  return a list of parallel transfomers to xfrm
  (needed because some transformers are modelled leg by leg)
  """

  activate_xfrm_byname(dss, xfrm) # activate the transformer
  bus_names = [s.split(".")[0] for s in dss.cktelement.bus_names]

  dss.circuit.set_active_bus(bus_names[0]) # activate the first bus

  connected_xfrms = [s.split(".")[1] for s in dss.bus.all_pde_active_bus if s.split(".")[0].lower() == "transformer"]

  out = []
  for t in connected_xfrms:
    activate_xfrm_byname(dss, t)
    if bus_names == [s.split(".")[0] for s in dss.cktelement.bus_names]:
      out.append(t)
  return out
  

def get_volt_stats(d:dict) -> dict:
  try:
    return {"min": np.min([v["vmin"]/(1000*v["basekv"]/SQRT3) for _,v in d.items()]),
            "max": np.max([v["vmax"]/(1000*v["basekv"]/SQRT3) for _,v in d.items()]),
            "diff": np.max([100*v["vdiff"]/(1000*v["basekv"]/SQRT3) for _,v in d.items()])}
  except ValueError:
    # if arrays are empty
    return {"min": None, "max": None, "diff": None}

def dict_key_comp(d:list[dict], key:str, f):
  """compare values in a list of dictionaries with the same key using function f
  None values are ignored
  """
  return f([i[key] for i in d if i[key] is not None])

def summary_outputs (d, pvbases, print=print):
  print ('\nSUMMARY of HOSTING CAPACITY ANALYSIS RESULTS\n')
  for key in ['converged', 'num_cap_switches', 'num_tap_changes', 'num_relay_trips', 'num_low_voltage', 'num_high_voltage']:
    print ('{:20s} {:>10s}'.format (key, str(d[key])))
  print ('Steady-State Voltage Extrema (DEPRECATED):')
  print ('  Vmin = {:8.4f} pu at {:s}'.format (d['vminpu'], d['node_vmin']))
  print ('  Vmax = {:8.4f} pu at {:s}'.format (d['vmaxpu'], d['node_vmax']))
  print ('Summary of Energy:')
  print ('  Net at Substation = {:12.2f} kWh'.format (d['kWh_Net']))
  print ('  Gross Load =        {:12.2f} kWh'.format (d['kWh_Load']))
  print ('  Losses =            {:12.2f} kWh'.format (d['kWh_Loss']))
  print ('  Photovoltaic =      {:12.2f} kWh'.format (d['kWh_PV']))
  print ('  Other DER =         {:12.2f} kWh'.format (d['kWh_Gen']))
  print ('  PV Reactive =       {:12.2f} kvarh'.format (d['kvarh_PV']))
  print ('Summary of Energy over Hosting Capacity:')
  print ('  Energy Exceeding Normal (EEN)=  {:12.2f} kWh'.format (d['kWh_EEN']))
  print ('  Unserved Energy (UE) =          {:12.2f} kWh'.format (d['kWh_UE']))
  print ('  Energy Over Normal Ratings =    {:12.2f} kWh (DEPRECATED)'.format (d['kWh_OverN']))
  print ('  Energy Over Emergency Ratings = {:12.2f} kWh (DEPRECATED)'.format (d['kWh_OverE']))

  columns = ''
  for key, row in d['pvdict'].items():
    columns = 'described by ' + str(row.keys())
    break
  print ('{:d} PV output rows {:s}'.format (len(d['pvdict']), columns))
  print ('\nTime-series Voltage Results:')
  volt_stats = get_volt_stats(d["voltdict"])
  pv_stats = get_volt_stats(d["pvdict"])
  rec_stats = get_volt_stats(d["recdict"])
  
  print ('  Minimum Voltage        = {:.4f} pu'.format(dict_key_comp([volt_stats, pv_stats, rec_stats], "min", np.min)))
  print ('  Maximum Voltage        = {:.4f} pu'.format(dict_key_comp([volt_stats, pv_stats, rec_stats], "max", np.max)))
  print ('  Maximum Voltage Change = {:.4f} %'.format(dict_key_comp([volt_stats, pv_stats, rec_stats], "diff", np.max)))
  if pv_stats["min"] is not None:
    print ('  Minimum PV Voltage        = {:.4f} pu'.format(pv_stats["min"]))
    print ('  Maximum PV Voltage        = {:.4f} pu'.format(pv_stats["max"]))
    print ('  Maximum PV Voltage Change = {:.4f} %'.format(pv_stats["diff"]))
  if len(d['recdict']) > 0:
    print ('\nRecloser Measurement Summary:')
    print ('                     P [kW]             Q[kvar]             V[V]              I[A]')
    print ('  Name            min      max       min      max       min      max      min     max')
    for key, row in d['recdict'].items():
      print ('  {:10s} {:8.2f} {:8.2f}  {:8.2f} {:8.2f}  {:8.2f} {:8.2f}  {:7.2f} {:7.2f}'.format (key[:10], 
                                                                                              row['pmin'], row['pmax'],
                                                                                              row['qmin'], row['qmax'],
                                                                                              row['vmin'], row['vmax'],
                                                                                              row['imin'], row['imax']))

def calc_total_een_ue(ditotals:pd.DataFrame) -> pd.Series:
  """perform integration of EEN and UE in the demand interval totals result"""
  return ditotals.transpose().dot(np.diff(np.insert(ditotals.index, 0, [0])))

def calc_di_voltage_stats(di_voltexception:pd.DataFrame, vmin=0.95, vmax=1.05, worst_case=False, **kwargs) -> pd.DataFrame:
  """calculate the voltage range for the time series data.
  Also calculates an integral of the deviation from the specified limits
  If Worst case is True, then limits are min(vmin_calc, vmin), max(vmax_calc, vmax) rather
  than simply reporting the limits directly.
  """
  vlimmin = di_voltexception.loc[:, ["MinVoltage", "MinLVVoltage"]].min()
  vlimmax = di_voltexception.loc[:, ["MaxVoltage", "MaxLVVoltage"]].max()
  if worst_case:
    vlimmin = vlimmin.apply(lambda x: min(vmin, x))
    vlimmax = vlimmax.apply(lambda x: max(vmax, x))
      
  return pd.concat([
            pd.concat([vlimmin, vlimmax]).rename("limits"),
            pd.concat([
                di_voltexception.loc[:, ["MinVoltage", "MinLVVoltage"]].applymap(lambda x: max(0, vmin - x)).transpose().dot(np.diff(np.insert(di_voltexception.index, 0, [0]))),
                di_voltexception.loc[:, ["MaxVoltage", "MaxLVVoltage"]].applymap(lambda x: max(0, x-vmax)).transpose().dot(np.diff(np.insert(di_voltexception.index, 0, [0])))
            ]).rename("integral")
          ], axis= 1)

def upgrade_line(dss:py_dss_interface.DSSDLL, change_lines:list, name:str, factor:float):
  dss.text(f"select line.{name}") # activate line obejct
  change_lines.append(f"edit line.{name} Length={dss.lines.length/factor:.7f} Normamps={dss.lines.norm_amps*factor:.2f} Emergamps={dss.lines.emerg_amps*factor:.2f}")

def upgrade_xfrm(dss:py_dss_interface.DSSDLL, change_lines:list, name:str, factor:float):
  # loop over any potential parallel transformers
  for xfrm in get_parallel_xfrm(dss, name):
    activate_xfrm_byname(dss, xfrm) #activate the transformer
    # loop over the windings and collect the kva ratings
    kvas = []
    for wdg in range(1, dss.transformers.num_windings+1):
      dss.transformers.wdg = wdg #activate the winding
      kvas.append(dss.transformers.kva)
    change_lines.append(f"edit transformer.{xfrm} kvas=({', '.join(str(round(s*factor)) for s in kvas)})")


class HCA:
  def __init__(self, inputs, logger_heading=None):
    self.inputs = inputs
    self.change_lines = []
    self.change_lines_noprint = []
    self.change_lines_history = []
    self.dss_reset = False
    self.logger = Logger(inputs["hca_log"]["logname"], 
                         level=inputs["hca_log"]["loglevel"], format=inputs["hca_log"]["format"])
    if inputs["hca_log"]["logtofile"]:
      self.logger.set_logfile(mode=inputs["hca_log"]["logtofilemode"])

    if logger_heading is not None:
      self.logger.info(logger_heading)
    self.print_config()

    ## establish a random seed for reproducibility
    # generate a 32bit seed based on the choice of feeder
    seed = int.from_bytes(hashlib.sha256(f'{inputs["choice"]}'.encode()).digest()[:4], 'little')
    # random.seed(hash(inputs["choice"]))
    self.random_state = np.random.RandomState(seed)

    ## load networkx graph
    self.load_graph()

    self.logger.info('\nLoaded Feeder Model {:s}'.format(self.inputs["choice"]))
    self.print_parsed_graph()

    ## initialize dss model
    self.dss = i2x.initialize_opendss(**self.inputs)
    self.update_basekv()

    ## create a set of voltage monitors throughout the feeder
    self.voltage_monitor()

    ## initialize structure for HCA analysis
    self.visited_buses = []
    self.exauhsted_buses = {"pv": [], "bat": [], "der": []}
    self.active_bus = None
    self.active_bus_kv = None
    self.cnt = 0 # iteration
    # Stotal is keyed by cnt (steps through HCA process)
    # Sij, hc, and eval are keyed by type -> node (i) -> cnt (step through HCA process)
    #      |--> note that these will be sparse since we only have info on a node if it is being altered 
    self.data = {"Stotal": {}, "Sij": {}, "hc": {}, "eval": {}}
    
    self.metrics = HCAMetrics(inputs["metrics"]["limits"], 
                              tol=inputs["metrics"]["tolerances"],
                              logger=self.logger)

  def print_config(self, level="info"):
    if level == "info":
      print_config(self.inputs, printf=self.logger.info)
    elif level == "debug":
      print_config(self.inputs, printf=self.logger.debug)

  def collect_stats(self):
    self.data["Stotal"][self.cnt] = pd.DataFrame({
      "pv": {k: sum(v[k] for v in self.graph_dirs["pvder"].values()) for k in ["kw", "kva"]},
      "bat": {k: sum(v[k] for v in self.graph_dirs["batder"].values()) for k in ["kw", "kva", "kwh"]},
      "der": {k: sum(v[k] for v in self.graph_dirs["gender"].values()) for k in ["kw", "kva"]}
    }).transpose()

  def update_data(self, key:str, typ:str, vals:dict):
    """Update the data storage values"""

    if key not in ["Sij", "hc", "eval"]:
      raise ValueError("key must be Sij, hc, or eval")
    if typ not in ["pv", "bat", "der"]:
      raise ValueError("Currently Only differentiating on pv, bat, der")
    
    if typ not in self.data[key]:
      self.data[key][typ] = {}  
    if self.active_bus not in self.data[key][typ]:
      self.data[key][typ][self.active_bus] = {}
    self.data[key][typ][self.active_bus][self.cnt] = copy.deepcopy(vals)
    
  def set_active_bus(self, bus):
    self.logger.info(f"Setting bus {bus} as active bus")
    self.active_bus = bus
    self.active_bus_kv = self.G.nodes[bus]["ndata"]["nomkv"]
    self.visited_buses.append(self.active_bus)

  def unset_active_bus(self):
    self.active_bus = None
    self.active_bus_kv = None
  
  def save_dss_state(self, tmp=False):
    """save the dss state, i.e. all the change lines"""
    # key = "tmp" if tmp else "nontmp"
    # self.change_lines_history[key]["print"].extend(copy.deepcopy(self.change_lines))
    # self.change_lines_history[key]["noprint"].extend(copy.deepcopy(self.change_lines_noprint))
    self.change_lines_history.extend(copy.deepcopy(self.change_lines + self.change_lines_noprint))
    self.clear_changelines()
  # def dss_state_nontmp2tmp(self):
  #   self.change_lines_history["tmp"] = copy.deepcopy(self.change_lines_history["nontmp"])

  def reset_dss(self, tmp=False):
    """recompile feeder and load changes from history"""
    # key = "tmp" if tmp else "nontmp"
    self.clear_changelines()
    self.dss = i2x.initialize_opendss(**self.inputs)
    for l in self.change_lines_history:
      self.dss.text(l)

  def clear_changelines(self):
    """clear change lines. Call between successive calls to rundss"""
    self.change_lines_noprint = []
    self.change_lines = []

  def replay_resource_addition(self, typ, bus, cnt):
          key = self.resource_key(typ, bus, cnt)
          self.new_capacity(typ, key, bus=bus, **self.data["Sij"][typ][bus][cnt])

  def resource_key(self, typ, bus, cnt):
    return f"{typ}_{bus}_cnt{cnt}"
  
  def update_basekv(self):
    for i,n in enumerate(self.dss.circuit.buses_names):
      self.dss.circuit.set_active_bus_i(i)
      basekv = self.dss.bus.kv_base*SQRT3
      if self.G.nodes[n]["ndata"]["nomkv"] == 0:
        self.G.nodes[n]["ndata"]["nomkv"] = basekv
      elif self.G.nodes[n]["ndata"]["nomkv"] != basekv:
          self.logger.warn(f'Base voltage for bus {n} is {basekv} kv, but graph has {self.G.nodes[n]["ndata"]["nomkv"]} kv. Updating')
          self.G.nodes[n]["ndata"]["nomkv"] = basekv
        

  def load_graph(self):
    self.G = i2x.load_builtin_graph(self.inputs["choice"])
    self.parse_graph()
    self.pv_voltage_base_list()
    self.comps, self.reclosers, self.comp2rec = isl.get_islands(self.G)

  def voltage_monitor(self):
    """Add voltage monitors throughout the system"""

    depth = 1
    while True:
      n = nx.descendants_at_distance(self.G, "sourcebus", depth)
      if not n:
          break
      n = [i for i in n if self.G.nodes[i]["ndata"]["shunts"]]
      if not n:
          depth += 1
          continue
      
      
      # ns = np.random.choice(n, 1)[0] 
      ns = n[self.random_state.randint(0, len(n))] 
      elem = self.G.nodes[ns]["ndata"]["shunts"][0] # select the first shunt
      self.change_lines_noprint.append(f"new monitor.{ns}_volt_vi element={elem} terminal=1 mode=96") # add a voltage monitor
      depth += 1 

  def parse_graph(self, summarize=False):
    """ parse the various categories of objects in the graph """
    self.graph_dirs = i2x.parse_opendss_graph(self.G, bSummarize=summarize)

  def show_component(self, i, printvals=True, printheader=False, plot=False, **kwargs):
    isl.show_component(self.G, self.comps, i, printvals=printvals, printheader=printheader, printfun=self.logger.info, plot=plot, **kwargs)

  def print_parsed_graph(self):
    self._print_parsed_graph(**self.graph_dirs)
  def _print_parsed_graph(self, pvder, gender, batder, largeder, resloads, bus3phase, all3phase, **kwargs):
    self.print_column_keys ('Large DER (>=100 kVA)', largeder)
    self.print_column_keys ('Generators', gender)
    self.print_column_keys ('PV DER', pvder)
    self.print_column_keys ('Batteries', batder)
    self.print_column_keys ('Rooftop Candidates (2ph & < 1kV)', resloads)
    # these are 3-phase buses without something else there, but the kV must be assumed
    self.print_column_keys ('Available 3-phase Buses', bus3phase)
    self.print_column_keys ('All 3-phase Buses', all3phase) 
    self.print_large_der()

  def print_column_keys (self, label, d):
    columns = ''
    for key, row in d.items():
      columns = 'described by ' + str(row.keys())
      break
    self.logger.info ('{:4d} {:20s} {:s}'.format (len(d), label, columns))
    
  def update_node_class(self, n):
    nclass  = "bus"
    try:
      if self.G.nodes[n]["ndata"]["shunts"]:
        nclass = self.G.nodes[n]["ndata"]["shunts"][-1].split(".")[0]
        if nclass == 'pvsystem':
          nclass = 'solar'
    except KeyError:
      pass
    return nclass

  def pv_voltage_base_list (self):
    """ create a list of pv voltage bases """
    self.pvbases = {}
    for d in [self.graph_dirs["pvder"], self.graph_dirs["largeder"]]:
      for key, row in d.items():  
        vnom = row['kv'] * 1000.0
        if row['phases'] > 1:
          vnom /= SQRT3
        self.pvbases[key] = vnom

  def print_large_der (self):
    self.logger.info('\nExisting DER:')
    for key, row in self.graph_dirs["largeder"].items():
      self.logger.info(f' {key} {row}')


  def append_rooftop_pv (self, pu_roofs=None, seed=None):
    """
    This function adds appropriately sized PV to 100*pu_roofs % of the residential loads.
    The optional seed argument for the random number generator can take either: 
      - None (default): Operating system defaults will be used
      - Int: any integer value will be passed directly to the seed function.
    """

    if seed is not None:
      self.random_state.seed(seed)

    if pu_roofs is None:
      pu_roofs = self.inputs["res_pv_frac"]

    rooftop_kw = 0.0
    rooftop_count = 0
    if (pu_roofs < 0.0) or (pu_roofs > 1.0):
      self.logger.error('Portion of PV Rooftops {:.4f} must lie between 0 and 1, inclusive'.format(pu_roofs))
    else:
      self.logger.info (f'\nAdding PV to {self.inputs["res_pv_frac"]*100}% of the residential rooftops that don\'t already have PV')
      for key, row in self.graph_dirs["resloads"].items():
        if self.random_state.random() <= pu_roofs:
          bus = row['bus']
          kv = row['kv']
          kw = row['derkw']
          kva = kw * 1.21 # TODO: Cat A or Cat B
          rooftop_kw += kw
          rooftop_count += 1
          self.change_lines.append('new pvsystem.{:s} bus1={:s}.1.2 phases=2 kv={:.3f} kva={:.2f} pmpp={:.2f} irrad=1.0 pf=1.0'.format (key, bus, kv, kva, kw))
          self.G.nodes[bus]["nclass"] = 'solar' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
          self.G.nodes[bus]["ndata"]["pvkva"] = kva
          self.G.nodes[bus]["ndata"]["pvkw"] = kw
          self.G.nodes[bus]["ndata"]["kv"] = kv
          self.G.nodes[bus]["ndata"]["shunts"].append(f"pvsystem.{key}")
    self.logger.info('Added {:.2f} kW PV on {:d} residential rooftops'.format(rooftop_kw, rooftop_count))
    self.parse_graph()
    self.pv_voltage_base_list()

  def remove_der(self, key, typ, bus):
    row = {"type": typ, "bus": bus}
    self.remove_large_der(key, row=row)

  def remove_large_der (self, key, row=None):
    ###TODO: the graph update is problematic if there are multiple resources at one bus
    if row is None:
      try:
        row = self.graph_dirs["largeder"][key]
      except KeyError:
        ## if der was already removed by some other method
        ## we could end up here
        return 
    if row['type'] == 'solar':
      self.change_lines.append('edit pvsystem.{:s} enabled=no'.format(key))
      self.G.nodes[row["bus"]]["ndata"]["pvkva"] = 0
      self.G.nodes[row["bus"]]["ndata"]["pvkw"] = 0
    elif row['type'] == 'storage':
      self.change_lines.append('edit storage.{:s} enabled=no'.format(key))
      self.G.nodes[row["bus"]]["ndata"]["batkva"] = 0
      self.G.nodes[row["bus"]]["ndata"]["batkw"] = 0
    elif row['type'] == 'generator':
      self.change_lines.append('edit generator.{:s} enabled=no'.format(key))
      self.G.nodes[row["bus"]]["ndata"]["genkva"] = 0
      self.G.nodes[row["bus"]]["ndata"]["genkw"] = 0
    else:
      return
    
    ## update graph (no need to return, G should be passed by reference)
    # remove the element from the shunt list
    sidx = np.where( [key in s for s in self.G.nodes[row["bus"]]["ndata"]["shunts"]])[0][0]
    self.G.nodes[row["bus"]]["ndata"]["shunts"].pop(sidx)
    self.G.nodes[row["bus"]]["nclass"] = self.update_node_class(row["bus"])

  def remove_all_pv(self):
    self.change_lines.append('batchedit pvsystem..* enabled=no')
    for n, d in self.G.nodes(data=True):
      if d.get("nclass") == 'solar':
        d["ndata"]["pvkva"] = 0.0
        d["ndata"]["pvkw"] = 0.0
        shunts_new = [s for s in d["ndata"]["shunts"] if 'pvsystem' not in s]
        d["ndata"]["shunts"] = shunts_new
        d["nclass"] = self.update_node_class(n)
  
  def disable_regulators(self):
    self.change_lines.append("batchedit regcontrol..* enabled=no")

  def sample_buslist(self, buslist:list, seed=None):
    """
    Sample list of buses.
    The optional seed argument for the random number generator can take either: 
      - None (default): Operating system defaults will be used
      - Int: any integer value will be passed directly to the seed function.
    """

    if seed is not None:
      self.random_state.seed(seed)

    return buslist[self.random_state.randint(0, len(buslist))]
    # return random.choice(buslist)

  def existing_resource_check(self, name, bus, valkey, val):
    if name in self.G.nodes[bus]["ndata"]["shunts"]:
      if val != self.G.nodes[bus]["ndata"][valkey]:
        self.logger.warn(f'Shunt {name} exists of bus {bus}, but {valkey} rating differs new {val} != old {self.G.nodes[bus]["ndata"][valkey]}')
        # remove, since it will be reinserted
        self.G.nodes[bus]["ndata"]["shunts"].pop(self.G.nodes[bus]["ndata"]["shunts"].index(name))
      else:
        return True # don't update the graph
    return False
  
  def append_large_pv(self, key):
    self._append_large_pv(key, **self.inputs["explicit_pv"][key])

  def _append_large_pv (self, key, bus, kv, kva, kw):
    self.change_lines.append('new pvsystem.{:s} bus1={:s} kv={:.3f} kva={:.3f} pmpp={:.3f} irrad=1'.format(key, bus, kv, kva, kw))
    self.pvbases[key] = 1000.0 * kv / SQRT3
    if not self.existing_resource_check(f"pvsystem.{key}", bus, "pvkva", kva):
      self.G.nodes[bus]["nclass"] = 'solar' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
      self.G.nodes[bus]["ndata"]["pvkva"] = kva
      self.G.nodes[bus]["ndata"]["pvkw"] = kw
      self.G.nodes[bus]["ndata"]["nomkv"] = kv
      self.G.nodes[bus]["ndata"]["shunts"].insert(0, f"pvsystem.{key}") #prepend to shunt list (make sure this is the first element found)

  def append_large_storage(self, key):
    self._append_large_storage(key, **self.inputs["explicit_storage"][key])

  def _append_large_storage (self, key, bus, kv, kva, kw, kwh):
    self.change_lines.append('new storage.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f} kwhrated={:.3f} kwhstored={:.3f}'.format(key, bus, kv, kva, kw, kwh, 0.5*kwh))
    if not self.existing_resource_check(f"storage.{key}", bus, "batkva", kva):
      self.G.nodes[bus]["nclass"] = 'storage' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
      self.G.nodes[bus]["ndata"]["batkva"] = kva
      self.G.nodes[bus]["ndata"]["batkw"] = kw
      self.G.nodes[bus]["ndata"]["batkwh"] = kwh
      self.G.nodes[bus]["ndata"]["nomkv"] = kv
      self.G.nodes[bus]["ndata"]["shunts"].insert(0, f"storage.{key}") #prepend to shunt list (make sure this is the first element found)

  def append_large_generator(self, key):
    self._append_large_generator(self, key, **self.inputs["explicit_generator"][key])
  def _append_large_generator (self, key, bus, kv, kva, kw):
    self.change_lines.append('new generator.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f}'.format(key, bus, kv, kva, kw))
    if not self.existing_resource_check(f"generator.{key}", bus, "genkva", kva):
      self.G.nodes[bus]["nclass"] = 'generator' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
      self.G.nodes[bus]["ndata"]["genkva"] = kva
      self.G.nodes[bus]["ndata"]["genkw"] = kw
      self.G.nodes[bus]["ndata"]["nomkv"] = kv
      self.G.nodes[bus]["ndata"]["shunts"].insert(0, f"generator.{key}") #prepend to shunt list (make sure this is the first element found)

  def redispatch_large_pv(self, key):
    self._redispatch_large_pv(key, **self.inputs["redisp_pv"][key])
  def _redispatch_large_pv (self, key, kva, kw):
    self.change_lines.append('edit pvsystem.{:s} kva={:.3f} pmpp={:.3f}'.format(key, kva, kw))
    bus = self.get_node_from_classkey("pvsystem", key)
    self.G.nodes[bus]["ndata"]["pvkva"] = kva
    self.G.nodes[bus]["ndata"]["pvkw"] = kw
  
  def redispatch_large_storage(self, key):
    self._redispatch_large_storage(key, **self.inputs["redisp_storage"][key])
  def _redispatch_large_storage (self, key, kva, kw, kwh):
    self.change_lines.append('edit storage.{:s} kva={:.3f} kw={:.3f} kwhrated={:.3f}'.format(key, kva, kw, kwh))
    bus = self.get_node_from_classkey("storage", key)
    self.G.nodes[bus]["ndata"]["batkva"] = kva
    self.G.nodes[bus]["ndata"]["batkw"] = kw

  def redispatch_large_generator(self, key):
    self._redispatch_large_generator(key, **self.inputs["redisp_gen"][key])
  def _redispatch_large_generator (self, key, kva, kw):
    self.change_lines.append('edit generator.{:s} kva={:.2f} kw={:.2f}'.format(key, kva, kw))
    bus = self.get_node_from_classkey("generator", key)
    self.G.nodes[bus]["ndata"]["genkva"] = kva
    self.G.nodes[bus]["ndata"]["genkw"] = kw

  def get_node_from_classkey(self, nclass, key):
    """Retrive the node name where shunt <nclass>.<key> is connected
    From graph G
    """
    
    for n, d in self.G.nodes(data=True):
      try:
        if np.any([f"{nclass}.{key}" == s for s in d["ndata"]["shunts"]]):
          return n
      except KeyError:
        pass
  
  def get_classkey_from_node(self, nclass, node):
    """Retrive the name of the object of type <nclass> connected at the given node
    Returns None if none is found
    """

    for s in self.G.nodes[node]["ndata"]["shunts"]:
      if s.split(".")[0] == nclass:
        return s.split(".")[1]
    return None

  def deterministic_changes(self):
    self.logger.info('Making some deterministic changes')
    ### remove all pv 
    if self.inputs["remove_all_pv"]:
      self.remove_all_pv()
      self.parse_graph()

    ### regulator controls
    if not self.inputs["reg_control"]:
      self.disable_regulators()
    
    ### remove specified large ders
    for key in self.inputs["remove_large_der"]:
      self.remove_large_der(key)
    self.parse_graph()
    
    ### add new specified storage
    for key in self.inputs["explicit_storage"]:
      self.append_large_storage(key)
    self.parse_graph()

    ### add new pv
    for key in self.inputs["explicit_pv"]:
      self.append_large_pv(key)
      self.parse_graph()
      self.pv_voltage_base_list()
    ### redispatch existing pv
    for key in self.inputs["redisp_pv"]:
      self.redispatch_large_pv(key)
    self.parse_graph()

    ### redispatch existing generators
    for key in self.inputs["redisp_gen"]:
      self.redispatch_large_generator(key)
    self.parse_graph()

    for ln in self.change_lines:
      self.logger.info (f' {ln}')    

  def rundss(self):
    pwd = os.getcwd()
    self.lastres = i2x.run_opendss(**{**{"change_lines": self.change_lines + self.change_lines_noprint, 
                                         "dss": self.dss, "demandinterval": True}, 
                                         **self.inputs} )  
    self.lastres["compflows"] = isl.all_island_flows(self.comp2rec, self.lastres["recdict"])
    os.chdir(pwd)
    self.read_di_outputs()

  def summary_outputs(self):
    summary_outputs(self.lastres, self.pvbases, print=self.logger.info)

  def read_di_outputs(self):
    path = os.path.join(self.dss.dssinterface.datapath, self.dss.circuit.name, "DI_yr_0")
    ### Thermal overloads
    df, cols = self._load_di(path, "DI_Overloads_1.CSV")
    cols.remove("Hour")
    cols.remove("Element")
    self.lastres["di_overloads"] = df.groupby("Element").agg('max').loc[:, cols]
    self.lastres["di_overloads"].index = self.lastres["di_overloads"].index.str.strip(' "') # remove spaces and quotes
    ### Voltage violations
    df, cols = self._load_di(path, "DI_VoltExceptions_1.CSV")
    self.lastres["di_voltexceptions"] = df.set_index("Hour")
    ### Totals (just use to keep finer grain track of EEN and UE for now)
    df, cols = self._load_di(path, "DI_Totals_1.CSV")
    cols = ["LoadEEN", "LoadUE"]
    self.lastres["di_totals"] = df.set_index("Time").loc[:, cols]

  def calc_total_een_ue(self, ditotals:pd.DataFrame):
    """perform integration of EEN and UE in the totals result"""
    return ditotals.transpose().dot(np.diff(np.insert(ditotals.index, 0, [0])))

  def _load_di(self, path:str, name:str) -> tuple[pd.DataFrame, list]:
    df = pd.read_csv(os.path.join(path, name))
    cols = [c.replace('"','').replace(' ','') for c in df.columns] # some cleanup
    df.columns = cols
    return df, cols
  
  def sample_capacity(self, typ):
    """sample unit capacity based on typ"""
    if typ == "pv":
      return self._sample_pv()
    elif typ == "bat":
      return self._sample_bat()
    elif typ == 'der':
      return self._sample_der()
    else:
      raise ValueError("Can only handle pv, bat, and der (gen) currently")

  def _sample_pv(self):
    """return a PV system with capacity between 50 kW and 1000 kW and pf 0.8"""
    kw = float(self.random_state.randint(50, 1001))
    kva = kw/0.8
    return {"kw": kw, "kva": kva}
  
  def _sample_bat(self):
    """return a 2 or 4 hour battery with capacity between 50 kW and 1000 kW and kVA"""
    kw = float(self.random_state.randint(50, 1001))
    kva = kw
    kwh = [2,4][self.random_state.randint(0,2)]
    # kwh = random.choice([2,4])*kw
    return {"kw": kw, "kva": kva, "kwh": kwh}

  def _sample_der(self):
    """TODO: for now just same as PV"""
    return self._sample_pv()

  def new_capacity(self, typ, key, bus=None, **kwargs):
    """create new capacity during hca round"""
    if bus is None:
      bus = self.active_bus
    kv = self.G.nodes[bus]["ndata"]["nomkv"]
    if typ == "pv":
      self._append_large_pv(key, bus, kv, **kwargs)
    elif typ == "bat":
      self._append_large_storage(key, bus, kv, **kwargs)
    elif typ == "der":
      self._append_large_generator(key, bus, kv, **kwargs)

  def alter_capacity(self, typ, key, **kwargs):
    """alter existing capacity during hca round"""
    if typ == "pv":
      self._redispatch_large_pv(key, **kwargs)
    elif typ == "bat":
      self._redispatch_large_storage(key, **kwargs)
    elif typ == "der":
      self._redispatch_large_generator(key, **kwargs)

  def get_hc(self, typ, bus, cnt=None):
    """Retrieve the hosting capacity stored for the given bus for the given type
    if no iteration counter is given the process works itself backwards from the
    current count until a viable index is found.
    """
    if cnt is not None:
      try:
        return self.data["hc"][typ][bus][cnt], cnt
      except KeyError:
        return None, cnt
    else:
      cnt = self.cnt
      while cnt >= 0:
        hc, cnt =  self.get_hc(typ, bus, cnt)
        if hc is None:
          cnt -= 1
        else:
          return hc, cnt
  

  def hca_round(self, typ, bus=None, Sij=None, allow_violations=False, hciter=True):
    """perform a single round of hca"""
    
    # if allow_violations is false iter must be true
    if (not allow_violations) and (not hciter):
      raise ValueError(f"hca_round: allow_violatios is {allow_violations} and hciter is {hciter}. Combination with allow_violations=False and hciter=False is not possible!")
    if not hciter:
      hc = "not calculated"
    #### some mappings
    nclass = {"pv": "pvsystem", "bat": "storage", "der": "generator"}
    graphdir = {"pv": "pvder", "bat": "batder", "der": "gender"}
    typmap = {"pv": "solar", "bat": "storage", "der": "generator"}

    # prep for new dss run
    self.save_dss_state()
    self.reset_dss()

     
    # first iteration of this round
    #### increment the count
    self.cnt +=1
    self.logger.info(f"========= HCA Round {self.cnt} ({typ})=================")
  
    #### Step 1: select a bus. Viable options (for now) are:
    # * graph_dirs["bus3phase"]: 3phase buses with nothing on them
    # * any bus already considered in a previous round (since the capacity added may not have been the limit)
    # * **exclude** buses that have zero hosting capacity
    if bus is None:
      buslist = [b for b in list(self.graph_dirs["bus3phase"]) + self.visited_buses if b not in self.exauhsted_buses[typ]]
      
      self.set_active_bus(self.sample_buslist(buslist))
    else:
      self.set_active_bus(bus)

    #### Step 2: Select new capacity, 
    ## there are two options:
    ## 1. this bus an evaluated hc -> use this value as the starting point
    ## 2. this has not been visited -> sample a capacity (add to existing (0 or otherwise))
    if Sij is not None:
      self.logger.info(f"Specified capacity: {Sij}")
    else:
      Sij = self.sample_capacity(typ)
      self.logger.debug(f"\tsampled {Sij}")
      keyexist = self.get_classkey_from_node(nclass[typ], self.active_bus)
      if keyexist is not None: 
        ## Option 1: check if bus already has resource of this type
        self.logger.debug(f"\tFound resource {keyexist}, at bus {bus}")
        hc, hc_cnt = self.get_hc(typ, self.active_bus)
        if hc is not None:
          # use the hc value
          self.logger.debug(f"\tLast hc info from round {hc_cnt}: {hc}")
          Sij = hc
        else:
          self.logger.debug(f"\tNo hc available, using sampled value")
          # for k in Sij.keys():
          #   Sij[k] += self.graph_dirs[graphdir[typ]][key][k]
          # self.logger.debug(f"\tNew sampled capacity: {Sij}")

      # self.alter_capacity(typ, key, **Sij)
    # else:
    #   ## Option 2: first time resource at this node
    key = self.resource_key(typ, self.active_bus, self.cnt) #f"{typ}-init-cnt{self.cnt}"
    self.logger.info(f"Creating new {typ} resource {key} with S = {Sij}")
    self.new_capacity(typ, key, **Sij)
    
    ### update graph structure and log changes
    self.parse_graph()
    for ln in self.change_lines:
      self.logger.debug (f' {ln}')

    ### Step 3: Solve
    self.rundss()
    if not self.lastres["converged"]:
      raise ValueError("Open DSS Run did not converge")

    ### Step 4: evaluate
    # evaluate the run with following options:
    # 1. no violations: fix capaity Sij, increment until violations occure to determine hc
    # 2. violations: decrease capacity until no violations. set hc=0 (mark bus as exauhsted)
    self.metrics.load_res(self.lastres)
    self.metrics.calc_metrics()
    if self.metrics.violation_count == 0:
      # no violations
      self.logger.info(f"No violations with capacity {Sij}.")
      self.update_data("Sij", typ, Sij)  # save installed capacity
      if hciter:
        self.logger.info("Iterating to find HC.")
        Sijlim = self.hc_bisection(typ, key, Sij, None) # find limit via bisection search
        hc = {k: Sijlim[k] - Sij[k] for k in ["kw", "kva"]}
        self.update_data("hc", typ, hc)
      self.update_data("eval", typ, self.metrics.eval)
    else:
      # violations: decrease capacity to find limit
      self.logger.info(f"Violations with capacity {Sij} (allow_violations is {allow_violations}).")
      self.logger.debug(f"\t\tviolations: {self.metrics.violation}")
      if allow_violations:
        self.update_data("Sij", typ, Sij)
        self.update_data("eval", typ, self.metrics.eval)
      if hciter:
        self.logger.info("Iterating to find Limit.")
        Sijlim = self.hc_bisection(typ, key, None, Sij)
        if Sijlim["kw"] == 0: 
          # no capacity at this bus (not just no *additional*, none at all)
          # remove the object from the graph
          self.logger.info(f"\tNo capacity at bus {self.active_bus}. Disabling resource {key}.")
          # self.remove_der(key, typmap[typ], self.active_bus) # dss command doesn't really matter, but this removes it from graph as well
          # self.reset_dss() # reset state to last good solution
        hc = {k: 0 for k in ["kw", "kva"]}
        self.update_data("hc", typ, hc)
        if not allow_violations:
          Sij = copy.deepcopy(Sijlim)
          self.update_data("Sij", typ, Sij) # update with intalled capacity
          self.update_data("eval", typ, self.metrics.eval)
      # mark bus as exauhsted
      self.exauhsted_buses[typ].append(self.active_bus)

    ### Step 5: final run with the actual capacity
    self.logger.info(f"*******Results for bus {self.active_bus} ({typ})\nSij = {Sij}\nhc = {hc}")
    self.remove_der(key, typmap[typ], self.active_bus) # dss command doesn't really matter, but this removes it from graph as well
    self.reset_dss() # reset state to last good solution
    if Sij["kw"] > 0:
      self.new_capacity(typ, key, **Sij)
    ### update graph structure and log changes
    self.parse_graph()
    for ln in self.change_lines:
      self.logger.info (f' {ln}')
    self.rundss()
    if not self.lastres["converged"]:
      raise ValueError("Open DSS Run did not converge")
    
    if allow_violations and hciter and (Sijlim["kw"] < Sij["kw"]):
      # violations are allowed an we installed capacity that will create some
      # recalculate metrics
      self.metrics.load_res(self.lastres)
      self.metrics.calc_metrics()

    ### cleanup
    self.unset_active_bus()
    self.collect_stats()

  def hc_bisection(self, typ, key, Sij1=None, Sij2=None, kwtol=5, kwmin=30):
    
    typmap = {"pv": "solar", "bat": "storage", "der": "generator"}
    #prep for new run
    self.remove_der(key, typmap[typ], self.active_bus) # dss command doesn't really matter, but this removes it from graph as well
    self.reset_dss()

    if (Sij1 is None) and (Sij2 is None):
      raise ValueError("At least one of lower or upper bound must be provided")

    if (Sij1 is not None) and (Sij2 is not None):
      # apply bisection on the kw value
      Sijnew = {"kw": (Sij1["kw"] + Sij2["kw"])/2}
      factor = Sijnew["kw"]/Sij1["kw"]
      for k in Sij1.keys():
        if k != "kw":
          Sijnew[k] = Sij1[k]*factor # apply to other properties proportionally 
    elif Sij2 is None:
      # unknown upperbound, double lower bound
      Sijnew = {k: 2*v for k, v in Sij1.items()}
    elif Sij1 is None:
      # unknown lower bound, half the upper bound
      Sijnew = {k: 0.5*v for k, v in Sij2.items()}
    
    self.new_capacity(typ, key, **Sijnew) #add the new capacity

    ### update graph structure and log changes
    self.parse_graph()
    for ln in self.change_lines:
      self.logger.debug (f' {ln}')

    ### Solve
    self.rundss()
    if not self.lastres["converged"]:
      raise ValueError("Open DSS Run did not converge")
    
    self.metrics.load_res(self.lastres)
    self.metrics.calc_metrics()
    if self.metrics.violation_count == 0:
      self.logger.info(f"\tNo violations with capacity {Sijnew}. Iterating to find HC")
      if Sij2 is None:
        # still uknown upper bound
        return self.hc_bisection(typ, key, Sijnew, None, kwtol, kwmin)
      elif Sij2["kw"] - Sijnew["kw"] < kwtol:
        # End criterion: no violations and search band within tolerance
        if Sijnew ["kw"] < kwmin:
          # if capacity is below a minimum threshold set to 0
          Sijnew = {k: 0 for k in Sijnew.keys()}
        return Sijnew
      else:
        # recurse and increase
        return self.hc_bisection(typ, key, Sijnew, Sij2, kwtol, kwmin)
    else:
      self.logger.info(f"\tViolations with capacity {Sijnew}. Iterating to find Limit.")
      self.logger.debug(f"\t\tviolations: {self.metrics.violation}")
      if Sijnew["kw"] < kwmin:
        # End criterion: upperbound is below minimum threshold set to 0 and exit
        return {k: 0 for k in Sijnew.keys()}
      elif Sij1 is None:
        # still unkonwn lower bound
        return self.hc_bisection(typ, key, None, Sijnew, kwtol, kwmin)
      else:
        # recurse and decrease
        return self.hc_bisection(typ, key, Sij1, Sijnew, kwtol, kwmin)
  
  def runbase(self, verbose=0):
    """runs an initial version of the feeder to establish a baseline.
    Metrics, for example will be evaluated w.r.t to this baseline as opposed
    to just the hard limits
    """
    ###########################################################################
    ##### Initialization
    ###########################################################################
    ### deterministic changes
    self.deterministic_changes()
    if verbose > 1:
      self.logger.info(f"\nFeeder description following deterministic changes:")
      self.print_parsed_graph()


    ### rooftop solar
    self.append_rooftop_pv()
    if verbose > 0:
      self.logger.info(f"\nFeeder description following intialization changes:")
      self.print_parsed_graph()

    if verbose > 1:
      self.logger.info('\nIslanding Considerations:\n')
      self.logger.info(f'{len(self.comps)} components found based on recloser positions')
      for i, c in enumerate(self.comps):
        self.show_component(i, printvals=True, printheader=i==0, plot=False)

    self.rundss()
    if verbose > 1:
      self.summary_outputs()

    self.collect_stats() #get intial loading
    self.metrics.set_base(self.lastres) # set baseline for metrics

    self.save_dss_state()

  def plot(self, **kwargs):
    i2x.plot_opendss_feeder(self.G, **kwargs)
class HCAMetrics:
  def __init__(self, lims:dict, comp=None, tol=None, logger=None):
    self.tests = {
      "voltage": {
      "vmin": self._vmin,
      "vmax": self._vmax,
      "vdiff": self._vdiff
      },
      "thermal": {
      "emerg": self._thermal
      },
      "island": {
        "pq": self._island_pq
      } 
    }
    if tol is None:
      tol = {k: 1e-3 for k in self.tests.keys()}

    if logger is not None:
      self.logger = logger
    self.base = None
    self.comp = comp
    self.load_lims(lims)
    self.eval = {}
    self.violation = {}
    self.violation_count = 0
    self.tol=tol
  
  def set_base(self, res:dict):
    self.base = HCAMetrics(self.lims, self.comp, self.tol)
    self.base.load_res(res, worst_case=True)

  def load_lims(self, lims:dict):
    self.lims = copy.deepcopy(lims)

  def clear_res(self):
    self.eval = {}
    self.violation = {}
    self.violation_count = 0

  def load_res(self, res:dict, **kwargs):
    self.clear_res()
    self.res = {k:copy.deepcopy(v) for k, v in res.items() if k != "dss"}
    self.volt_stats = calc_di_voltage_stats(res["di_voltexceptions"], **self.lims["voltage"], **kwargs)
    self.vdiff = dict_key_comp([get_volt_stats(res[k]) for k in ["voltdict", "pvdict", "recdict"]], "diff", np.max)
    # self.volt_stats = get_volt_stats(res["voltdict"])
    # self.pv_stats = get_volt_stats(res["pvdict"])
    # self.rec_stats = get_volt_stats(res["recdict"])
  
  def get_volt_max_buses(self, threshold):
    d = {}
    for reskey in 'pvdict', 'recdict', 'voltdict':
      for k, v  in self.res[reskey].items():
          if v["vmax"]/(1000*v["basekv"]/np.sqrt(3)) > threshold:
              d[k] = v["v"]
    return d

  def get_volt_min_buses(self, threshold):
    d = {}
    for reskey in 'pvdict', 'recdict', 'voltdict':
      for k, v  in self.res[reskey].items():
          if v["vmin"]/(1000*v["basekv"]/np.sqrt(3)) < threshold:
              d[k] = v["v"]
    return d

  # def _test(self, test:bool, margin, description:str) -> tuple[bool, str]:
  def _test(self, val, lim, sense, tol) -> tuple[bool, float, str]:
    """
    sense = 1 -> val should be greater than lim -> margin is positive if successful, negative is violation
    
    sense = -1 -> val should be less than lim -> margin is still positive if successful (mult by -1), negative is violation
    """
    margin = sense*(val - lim)
    return margin >= (0 - tol), margin
    
  def _vmin(self, val):
    vmin = self.volt_stats.loc[self.volt_stats.index.str.contains("Min"), :]
    # vmin = dict_key_comp([self.volt_stats, self.pv_stats, self.rec_stats], "min", np.min)
    test, margin = self._test(vmin["limits"], val, 1, self.tol["voltage_mag"])
    if test.all() or (self.base is None):
      # test passed
      return test, margin
    else:
      # test didn't pass, compare to base result
      lims = self.base.volt_stats.loc[self.base.volt_stats.index.str.contains("Min"),:]
      test1, margin1 = self._test(vmin["limits"], lims["limits"], 1, self.tol["voltage_mag"]) #new vmin should be >= base solution
      test2, margin2 = self._test(vmin["integral"], lims["integral"], -1, self.tol["voltage_integral"]) #integral of vmin violation should be <= base solution
      return pd.concat([test1, test2], axis=1), pd.concat([margin1, margin2], axis=1)
  
  def _vmax(self, val):
    # vmax = dict_key_comp([self.volt_stats, self.pv_stats, self.rec_stats], "max", np.max)
    vmax = self.volt_stats.loc[self.volt_stats.index.str.contains("Max"), :]
    test, margin = self._test(vmax["limits"], val, -1, self.tol["voltage_mag"])
    if test.all() or (self.base is None):
      # test passed
      return test, margin
    else:
      # test didn't pass, compare to base result
      lims = self.base.volt_stats.loc[self.base.volt_stats.index.str.contains("Max"),:]
      test1, margin1 = self._test(vmax["limits"], lims["limits"], -1, self.tol["voltage_mag"]) #new vamx should be <= base solution
      test2, margin2 = self._test(vmax["integral"], lims["integral"], -1, self.tol["voltage_integral"]) #integral of vmax violation should be <= base solution
      return pd.concat([test1, test2], axis=1), pd.concat([margin1, margin2], axis=1)
  
  def _vdiff(self, val):
    if self.base is not None:
      val = max(val, self.base.vdiff)
    return self._test(self.vdiff, val, -1, self.tol["voltage_diff"])
  
  def _ue(self, val):
    # verifies that the total ue d
    return self._test(self.res["kWh_UE"], val, -1, self.tol["thermal"])
  
  def _thermal(self, val):
    if self.base is None:
      ## test 2: no new overloaded branches (i.e. no loading > 100% emergency)
      ov2 = self.res["di_overloads"].loc[:, "%Emerg"]  #<-- should be empty
      if ov2.empty:
        return True, 0 #no real margin to speak of in this case
      else:
        return self._test(self.res["di_overloads"]["%Emerg"], 100, -1, self.tol["thermal"])
    else:
      mask = self.res["di_overloads"].index.isin(self.base.res["di_overloads"].index)
      ## test 1: any of the overloaded branches in base solution are not *more* overloaded
      ov1 = self.base.res["di_overloads"]["%Emerg"].subtract(self.res["di_overloads"].loc[:,"%Emerg"]).dropna()
      test1, margin1 = self._test(ov1, 0, 1, self.tol["thermal"])
      ## test 2: no new overloaded branches (i.e. no loading > 100% emergency)
      ov2 = self.res["di_overloads"].loc[~mask, "%Emerg"]  #<-- should be empty
      test2, margin2 = self._test(ov2, 100, -1, self.tol["thermal"])
      return pd.concat([test1, test2]), pd.concat([margin1[~test1], margin2[~test2]])

  def _all_comps(self, func, *args):
    """Loop through all components, return first error"""
    for i in self.res["compflows"].keys():
      out = func(*args, i=i)
      if not out[0]:
        return out
    return out
  
  # def _island_dir(self, val, pq:str, i=None):
  def _island_dir(self):
    """Test if flow in/out of component is in total in same direction"""
    # igonroing i and pq for now
    # self.res["compflows"][i]["lims"].loc[["min", "max"], pq] -> the minimum and maximum p or q flow for component
      #   \-> take the sign -> leads to array of [1, -1, etc.] of length 2
      #   \-> take the sum: options are 2, -2 (both in same direction), 0 (opposite direction), 1 or -1 (unlikely, one element is exactly 0)
      #   \-> take abs and subtract 1. If this is greater than 0 then both were in the same direction.
    test = pd.concat([ 
      pd.Series({i: np.abs(self.res["compflows"][i]["lims"].loc[["min", "max"], pq].apply(np.sign).sum()) 
                 for i in self.res["compflows"].keys()}, name=f"{pq}_dir")
                 for pq in ["p", "q"]], axis=1)
    return self._test(test, 0, 1, self.tol["island"])
    if i is not None:
      # self.res["compflows"][i]["lims"].loc[["min", "max"], pq] -> the minimum and maximum p or q flow for component
      #   \-> take the sign -> leads to array of [1, -1, etc.] of length 2
      #   \-> take the sum: options are 2, -2 (both in same direction), 0 (opposite direction), 1 or -1 (unlikely, one element is exactly 0)
      #   \-> take abs and subtract 1. If this is greater than 0 then both were in the same direction.
      test = np.abs(self.res["compflows"][i]["lims"].loc[["min", "max"], pq].apply(np.sign).sum()) - 1
      return self._test(test, 0, 1, self.tol["island"])
    else:
      return self._all_comps(self._island_dir, val, pq)
    
  # def _island_frac(self, val:list[float], pq:str, i=None):
  def _island_frac(self, val:list[float]):
    """get the ratio between the minimum magnitude flow in/out of region to the maximum flow
    val = [p_frac_limit, q_frac_limit]
    """
    test = pd.concat([
      pd.Series({i: self.res["compflows"][i]["lims"].transpose().apply(lambda x: x.minabs/np.max([np.abs(x["min"]), np.abs(x["max"])]), axis=1)[pq] 
                 for i in self.res["compflows"].keys()}, name=f"{pq}_frac")
                 for pq in ["p", "q"]], axis=1)
    # Note that test is a comp x 2 sized DataFrame. when we subtract a list lenght 2
    # from this, it will subract the first entry from the first colum and the second from the second column.
    return self._test(test, val, 1, self.tol["island"])
    if i is not None:
      test = self.res["compflows"][i]["lims"].transpose().apply(lambda x: x.minabs/np.max([np.abs(x["min"]), np.abs(x["max"])]), axis=1)[pq]
      return self._test(test, val, 1, self.tol["island"])
    else:
      return self._all_comps(self._island_frac, val, pq)
  
  def _island_test(self, val, pq:str):
     test, margin = self._island_dir(val, pq, i=self.comp)
     if np.all(test):
       # all direction tests passed, no need to continue
       return test, margin
     
     test, margin = self._island_frac(val, pq, i=self.comp)
     return test, margin

  def _island_pq_old(self, vals):
      ptest, pmargin = self._island_test(vals[0], "p")
      if np.all(ptest):
        # p tests passed, no need to check q
        return ptest, pmargin

      ## p test failed, check q as well
      return self._island_test(vals[1], "q")
  
  def _island_pq(self, vals):
    """
    Screen for potential islanding
    screen 1: p flows never reverse for any component
    screen 2: (if 1 fails) the ratio of minimum to maximum p flow 
              is above threshold, i.e. component is not too close to being an island
    screen 3: same as screen 1 but for q
    screen 4: same as screen 2 but for q
    """
    dirtest, dirmargin = self._island_dir()
    fractest, fracmargin = self._island_frac(vals)
    test = pd.concat([dirtest, fractest], axis=1)
    margin = pd.concat([dirmargin, fracmargin], axis=1)

    if np.all(test["p_dir"]):
      # screen 1 passes : p never reverses direction
      return True, margin
    elif np.all(test["p_frac"]):
      # screen 2 passes: p is always sufficiently large in magnitude
      return True, margin
    elif np.all(test["q_dir"]):
      # screen 3 passes : q never reverses direction
      return True, margin
    elif np.all(test["q_frac"]):
      # screen 4 passes: q is always suffiently large in magnitude
      return True, margin
    else:
      # test failed
      return False, margin


  def calc_metrics(self, verbose=0):
    violation_count = 0
    for metric_class, metrics in self.lims.items():
      self.eval[metric_class] = {}
      for metric, val in metrics.items():
        test, margin = self.tests[metric_class][metric](val)
        if (self.logger is not None) and (verbose > 0):
          self.logger.debug(f"metric={metric}, val={val}, test result = {test}, margin = {margin}")
        self.eval[metric_class][metric] = margin
        if not np.all(test):
          if metric_class not in self.violation.keys():
            self.violation[metric_class] = {}

          self.violation[metric_class][metric] = margin
          violation_count += 1
    self.violation_count = violation_count
        
        


def print_options():
  print ('Feeder Model Choices for HCA')
  print ('Feeder       Path                 Base File')
  for key, row in i2x.feederChoices.items():
    print ('{:12s} {:20s} {:s}'.format (key, row['path'], row['base']))
  print ('\nSolar Profile Choices:', i2x.solarChoices.keys())
  print ('Load Profile Choices:', i2x.loadChoices.keys())
  print ('Inverter Choices:', i2x.inverterChoices.keys())
  print ('Solution Mode Choices:', i2x.solutionModeChoices)
  print ('Control Mode Choices:', i2x.controlModeChoices)


def load_config(configin):
  ### get defaults
  defaultsconfig = os.path.join(os.path.dirname(os.path.realpath(__file__)), "defaults.json")
  with open(defaultsconfig) as f:
    inputs = json.load(f)
  
  if os.path.basename(configin) != 'defaults.json':
    with open(configin) as f:
      config = json.load(f)
    merge_configs(inputs, config)
  return inputs

def main(inputs):
  ### create hca object
  hca = HCA(inputs)
  
  ###########################################################################
  ##### Initialization
  ###########################################################################
  ### deterministic changes
  hca.deterministic_changes()
  hca.logger.info(f"\nFeeder description following deterministic changes:")
  hca.print_parsed_graph()


  ### rooftop solar
  hca.append_rooftop_pv()
  hca.logger.info(f"\nFeeder description following intialization changes:")
  hca.print_parsed_graph()

  hca.logger.info('\nIslanding Considerations:\n')
  hca.logger.info(f'{len(hca.comps)} components found based on recloser positions')
  for i, c in enumerate(hca.comps):
    hca.show_component(i, printvals=True, printheader=i==0, plot=False)

  hca.rundss()
  hca.summary_outputs()
  return hca
   
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="i2X Hosting Capacity Analysis")
  parser.add_argument("config", nargs='?', help="configuration file", default="defaults.json")
  parser.add_argument("--show-options", help="Show options and exit", action='store_true')
  parser.add_argument("--print-inputs", help="print passed inputs", action="store_true")
  parser.add_argument("--show-defaults", help="show default configuration and exit", action='store_true')
  args = parser.parse_args()

  if args.show_options:
    print_options()
    sys.exit(0)

  if args.show_defaults:
    inputs = load_config('defaults.json')
    print_config(inputs)
    sys.exit(0)
  
  inputs = load_config(args.config)
  
  if args.print_inputs:
    print("Provided/Default Inputs:\n===============")
    for k,v in inputs.items():
      print(f"{k}: {v}")
  
  hca = main(inputs)


