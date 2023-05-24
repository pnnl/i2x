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

SQRT3 = math.sqrt(3.0)

def print_column_keys (label, d):
  columns = ''
  for key, row in d.items():
    columns = 'described by ' + str(row.keys())
    break
  print ('{:4d} {:20s} {:s}'.format (len(d), label, columns))


def check_element_status(dss:py_dss_interface.DSSDLL, elemname:str) -> int:
  index_str = dss.circuit_set_active_element(elemname)
  return dss.cktelement_read_enabled()

def activate_monitor_byname(dss:py_dss_interface.DSSDLL, monitorname:str) -> int:
  """
  activate monitor, return 0 if monitor not found
  """

  idx = dss.monitors_first()
  while idx > 0:
    if monitorname == dss.monitors_read_name():
      return idx
    idx = dss.monitors_next()
  return idx
  

def activate_monitor_byelem(dss:py_dss_interface.DSSDLL, elemname:str, mode:int) -> int:
  """
  activate monitor, return 0 if monitor not found
  """

  idx = dss.monitors_first()
  while idx > 0:
    if (elemname == dss.monitors_read_element()) and (mode == dss.monitors_read_mode()):
      return idx
    idx = dss.monitors_next()
  return idx

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
  pv_vmin = 100.0
  pv_vmax = 0.0
  pv_vdiff = 0.0

  # print("key             vbase        vmin        vmax")
  # print("------------  ----------  ----------  ----------")

  for key, row in d['pvdict'].items():
    if key in pvbases:
      v_base = pvbases[key]
    else:
      if check_element_status(d["dss"], f"pvsystem.{key}") == 0:
        ## element is not enabled -> skip
        continue
      v_base = 120.0
    row['vmin'] /= v_base
    row['vmax'] /= v_base
    row['vmean'] /= v_base
    row['vdiff'] /= v_base
    row['vdiff'] *= 100.0
    # print(f"{key:12s}  {v_base:10.2f}  {row['vmin']:10.2f}  {row['vmax']:10.2f}")
    if row['vmin'] < pv_vmin:
      pv_vmin = row['vmin']
    if row['vmax'] > pv_vmax:
      pv_vmax = row['vmax']
    if row['vdiff'] > pv_vdiff:
      pv_vdiff = row['vdiff']
  print ('  Minimum PV Voltage        = {:.4f} pu'.format(pv_vmin))
  print ('  Maximum PV Voltage        = {:.4f} pu'.format(pv_vmax))
  print ('  Maximum PV Voltage Change = {:.4f} %'.format(pv_vdiff))
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

class HCA:
  def __init__(self, inputs):
    self.inputs = inputs
    self.change_lines = []
    self.logger = Logger(inputs["hca_log"]["logname"], 
                         level=inputs["hca_log"]["loglevel"], format=inputs["hca_log"]["format"])
    if inputs["hca_log"]["logtofile"]:
      self.logger.set_logfile()

    ## load networkx graph
    self.load_graph()

    self.logger.info('\nLoaded Feeder Model {:s}'.format(self.inputs["choice"]))
    self.print_parsed_graph()

    ## initialize dss model
    self.dss = i2x.initialize_opendss(**self.inputs)
    self.update_basekv()

  def update_basekv(self):
    for i,n in enumerate(self.dss.circuit_all_bus_names()):
      self.dss.circuit_set_active_bus_i(i)
      basekv = self.dss.bus_kv_base()*SQRT3
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
      - 'hash': the hash of graph G, will be used as the seed.
                          As a result, calls on exactly the same graph will be reproducible.
      - Int: any integer value will be passed directly to the seed function.
    """

    if seed == 'hash':
      random.seed(hash(self.G))
    else:
      random.seed(seed)

    if pu_roofs is None:
      pu_roofs = self.inputs["res_pv_frac"]

    rooftop_kw = 0.0
    rooftop_count = 0
    if (pu_roofs < 0.0) or (pu_roofs > 1.0):
      self.logger.error('Portion of PV Rooftops {:.4f} must lie between 0 and 1, inclusive'.format(pu_roofs))
    else:
      self.logger.info (f'\nAdding PV to {self.inputs["res_pv_frac"]*100}% of the residential rooftops that don\'t already have PV')
      for key, row in self.graph_dirs["resloads"].items():
        if random.random() <= pu_roofs:
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

  def remove_large_der (self, key):
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

  def append_large_pv(self, key):
    self._append_large_pv(key, **self.inputs["explicit_pv"][key])

  def _append_large_pv (self, key, bus, kv, kva, kw):
    self.change_lines.append('new pvsystem.{:s} bus1={:s} kv={:.3f} kva={:.3f} pmpp={:.3f} irrad=1'.format(key, bus, kv, kva, kw))
    self.pvbases[key] = 1000.0 * kv / SQRT3
    self.G.nodes[bus]["nclass"] = 'solar' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
    self.G.nodes[bus]["ndata"]["pvkva"] = kva
    self.G.nodes[bus]["ndata"]["pvkw"] = kw
    self.G.nodes[bus]["ndata"]["nomkv"] = kv
    self.G.nodes[bus]["ndata"]["shunts"].append(f"pvsystem.{key}")

  def append_large_storage(self, key):
    self._append_large_storage(key, **self.inputs["explicit_storage"][key])

  def _append_large_storage (self, key, bus, kv, kva, kw, kwh):
    self.change_lines.append('new storage.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f} kwhrated={:.3f} kwhstored={:.3f}'.format(key, bus, kv, kva, kw, kwh, 0.5*kwh))
    self.G.nodes[bus]["nclass"] = 'storage' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
    self.G.nodes[bus]["ndata"]["batkva"] = kva
    self.G.nodes[bus]["ndata"]["batkw"] = kw
    self.G.nodes[bus]["ndata"]["batkwh"] = kwh
    self.G.nodes[bus]["ndata"]["nomkv"] = kv
    self.G.nodes[bus]["ndata"]["shunts"].append(f"storage.{key}")

  def append_large_generator(self, key):
    self._append_large_generator(self, key, **self.inputs["explicit_generator"][key])
  def append_large_generator (self, key, bus, kv, kva, kw):
    self.change_lines.append('new generator.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f}'.format(key, bus, kv, kva, kw))
    self.G.nodes[bus]["nclass"] = 'generator' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
    self.G.nodes[bus]["ndata"]["genkva"] = kva
    self.G.nodes[bus]["ndata"]["genkw"] = kw
    self.G.nodes[bus]["ndata"]["nomkv"] = kv
    self.G.nodes[bus]["ndata"]["shunts"].append(f"generator.{key}")

  def redispatch_large_pv(self, key):
    self._redispatch_large_pv(key, **self.inputs["redisp_pv"][key])
  def _redispatch_large_pv (self, key, kva, kw):
    self.change_lines.append('edit pvsystem.{:s} kva={:.2f} pmpp={:.2f}'.format(key, kva, kw))
    bus = self.get_node_from_classkey("pvsystem", key)
    self.G.nodes[bus]["ndata"]["pvkva"] = kva
    self.G.nodes[bus]["ndata"]["pvkw"] = kw
  
  def redispatch_large_storage(self, key):
    self._redispatch_large_storage(key, **self.inputs["redisp_storage"][key])
  def _redispatch_large_storage (self, key, kva, kw):
    self.change_lines.append('edit storage.{:s} kva={:.2f} kw={:.2f}'.format(key, kva, kw))
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

  def deterministic_changes(self):
    self.logger.info('Making some deterministic changes')
    ### remove all pv 
    if self.inputs["remove_all_pv"]:
      self.remove_all_pv()
      self.parse_graph()
    
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

    ### redispatch existing generators
    for key in self.inputs["redisp_gen"]:
      self.redispatch_large_generator(key)
    
    self.parse_graph()
    for ln in self.change_lines:
      self.logger.info (f' {ln}')    

  def rundss(self):
    pwd = os.getcwd()
    self.lastres = i2x.run_opendss(**{**{"change_lines": self.change_lines, "dss": self.dss}, **self.inputs} )  
    os.chdir(pwd)
    
  def summary_outputs(self):
    summary_outputs(self.lastres, self.pvbases, print=self.logger.info)


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
  args = parser.parse_args()

  if args.show_options:
    print_options()
    sys.exit(0)
  
  inputs = load_config(args.config)
  
  if args.print_inputs:
    print("Provided/Default Inputs:\n===============")
    for k,v in inputs.items():
      print(f"{k}: {v}")
  
  hca = main(inputs)


