from __future__ import annotations
import i2x.api as i2x
from importlib import resources
import math
import networkx as nx
import json
import i2x.der_hca.islands as isl
import numpy as np
import py_dss_interface
from .hca_utils import Logger, merge_configs, ProcessTime
import os
import pandas as pd
import copy
import shutil
import hashlib
import pickle
from typing import Union
import i2x.der_hca.upgrade_costs as upcst

### Cost objects
conductor_cost = upcst.ConductorCosts()
xfrm_cost = upcst.TransformerCosts()
reg_cost = upcst.RegulatorCosts()
hca_options = {"time_series": "Single HC value calculated via quasi-steady state time series solution",
                "sequence": "Sequency of HC calculated over time"}
SQRT3 = math.sqrt(3.0)
pd_version = [int(s) for s in pd.__version__.split(".")]

def print_config(config:dict, tabs="", printf=print, title="Configuration"):
    """print a configuration dictionary"""
    if not tabs:
      printf(f"\n===================================\n{title}:\n===================================")
    for k, v in config.items():
        if isinstance(v, dict):
            printf(f"{tabs}{k}:")
            print_config(v, tabs=tabs+"\t", printf=printf)
        else:
            if isinstance(v, (pd.DataFrame, pd.Series)):
              printf(f"{tabs}{k}:")
              printf(v)
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

def get_regcontrol(dss:py_dss_interface.DSSDLL, xfrm:str) -> int:
  """
  activate the regulator controller, returns 0 if no control is found
  """
  idx = dss.regcontrols.first()
  while idx > 0:
    if dss.regcontrols.transformer == xfrm:
      return idx
    idx = dss.regcontrols.next()
  return idx

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
  if (pd_version[0]) > 1 and (pd_version[1]) > 0:
    # use pd.DataFrame.map
    integral = pd.concat([
                di_voltexception.loc[:, ["MinVoltage", "MinLVVoltage"]].map(lambda x: max(0, vmin - x)).transpose().dot(np.diff(np.insert(di_voltexception.index, 0, [0]))),
                di_voltexception.loc[:, ["MaxVoltage", "MaxLVVoltage"]].map(lambda x: max(0, x-vmax)).transpose().dot(np.diff(np.insert(di_voltexception.index, 0, [0])))
            ]).rename("integral")
  else:
    # use pd.DataFrame.applymap
    integral = pd.concat([
                di_voltexception.loc[:, ["MinVoltage", "MinLVVoltage"]].applymap(lambda x: max(0, vmin - x)).transpose().dot(np.diff(np.insert(di_voltexception.index, 0, [0]))),
                di_voltexception.loc[:, ["MaxVoltage", "MaxLVVoltage"]].applymap(lambda x: max(0, x-vmax)).transpose().dot(np.diff(np.insert(di_voltexception.index, 0, [0])))
            ]).rename("integral")  
  return pd.concat([
            pd.concat([vlimmin, vlimmax]).rename("limits"),
            integral
          ], axis= 1)

def upgrade_line(dss:py_dss_interface.DSSDLL, change_lines:list, name:str, factor:float=2):
  """Decrease length and increase rating by factor (intended to simulate e.g. paralleling line of line (factor=2)) """
  dss.text(f"select line.{name}") # activate line obejct
  change_lines.append(f"edit line.{name} Length={dss.lines.length/factor:.7f} Normamps={dss.lines.norm_amps*factor:.2f} Emergamps={dss.lines.emerg_amps*factor:.2f}")
  return {"old": dss.lines.norm_amps, "new": dss.lines.norm_amps*factor}

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
    return {"old": kvas, "new": [round(s*factor) for s in kvas]}

def change_xfrm_tap(dss:py_dss_interface.DSSDLL, change_lines:list, name:str, tapchange:int):
  """
  Change the tap settings of the transformer.
  Note: this assumes taps on winding 1 for now.
  """
  for xfrm in get_parallel_xfrm(dss, name):
    activate_xfrm_byname(dss, xfrm) #activate the transformer
    dss.transformers.wdg = 1 # activate winding 1
    ntaps = dss.transformers.num_taps/2 #dividing by 2 to because we're splitting by up/down
    tap = dss.transformers.tap
    if tapchange < 0:
      pu_range = 1.0 - dss.transformers.min_tap
    else:
      pu_range = dss.transformers.max_tap - 1.0 
    change_lines.append(f"edit transformer.{xfrm} wdg={dss.transformers.wdg} tap={tap + pu_range*tapchange/ntaps}")
    return {"old": tap, "new": tap + pu_range*tapchange/ntaps}
  
def change_regulator_vreg(dss:py_dss_interface.DSSDLL, change_lines:list, name:str, vregchange:int,
                          printf=print):
  for xfrm in get_parallel_xfrm(dss, name):
    activate_xfrm_byname(dss, xfrm) #activate the transformer
    err = get_regcontrol(dss, xfrm) # activate the control
    if err <= 0:
        raise ValueError(f"Didn't find a controller for {xfrm}")
    # activate transformer winding controlled by the regulator
    dss.transformers.wdg = dss.regcontrols.winding
    vbase = (1000*dss.transformers.kv)
    pt = dss.regcontrols.pt_ratio
    vreg_min = np.floor(0.95*vbase/pt)
    vreg_max = np.ceil(1.05*vbase/pt)
    vreg = dss.regcontrols.forward_vreg
    vreg_pu = vreg*pt/vbase
    vreg_new = vreg + vregchange
    if vreg_new < vreg_min:
      printf(f"new vreg < vreg min {vreg_min}: setting to minimum.")
      vreg_new = vreg_min
    elif vreg_new > vreg_max:
      printf(f"new vreg > vreg max {vreg_max}: setting to maximum.")
      vreg_new = vreg_max
    change_lines.append(f"edit regcontrol.{dss.regcontrols.name} vreg={vreg_new} revvreg={vreg_new}")
  return {"old": vreg, "old_pu": vreg_pu, "new": vreg_new, "new_pu": vreg_new*pt/vbase}

def read_regulator_shape(f:str) -> pd.DataFrame:
    """read a regulator tap settings shape into a pandas series
    indexed on (hr, sec)
    NOTE: it is assumed that FIRST 4 columns are "hr", "sec", "wdg", and "tap_pu"
    """
    df = pd.read_csv(f) # read file with shape
    # update columns based on specified input configuration
    # 
    df.columns = ["hr", "sec", "wdg", "tap_pu"] + list(df.columns)[4:]
    df.set_index(["hr", "sec"], inplace=True)
    return df.loc[:, ["wdg","tap_pu"]]

def get_xfrm_kvas(dss:py_dss_interface.DSSDLL, name:str):
  # loop over any potential parallel transformers
  for xfrm in get_parallel_xfrm(dss, name):
    activate_xfrm_byname(dss, xfrm) #activate the transformer
    # loop over the windings and collect the kva ratings
    kvas = []
    for wdg in range(1, dss.transformers.num_windings+1):
      dss.transformers.wdg = wdg #activate the winding
      kvas.append(dss.transformers.kva)
  return kvas

def get_xfrm_phase(dss:py_dss_interface.DSSDLL, xfrm:str):
  activate_xfrm_byname(dss, xfrm) #activate the transformer
  # initialize some large nphase number (we always take minimum)
  nphase = 100000
  ### loop over buses and get their phase (node) number
  for n in dss.cktelement.bus_names:
    dss.circuit.set_active_bus(n) #set bus active
    nphase = min(nphase, dss.bus.num_nodes)
  return nphase

def next_xfrm_kva(kva, nphase, skip=0) -> float:
  """get the next kva transformer rating
  skip is an optional parameter to skip to greater ratings.
  When skip=0 [default] the next available rating is chosen.
  When skip=1 one ratings will be skipped, etc.
  """

  # ratings from https://github.com/GRIDAPPSD/Powergrid-Models/blob/feature/SETO/taxonomy/FixTransformers.py
  if nphase > 1:
    # three phase
    ratings = np.array([30, 45, 75, 112.5, 150, 225, 300, 500, 750, 1000, 1500, 2000, 3750, 5000, 7500, 10000])
  else:
    # single phase
    ratings = np.array([5, 10, 15, 25, 37.5, 50, 75, 100, 167, 250, 333, 500])

  # multiplication by 1.1 is sort of like a minumum upgrade. 
  # also makes sure that the first found entry is not the one equal to kva.
  try:
    return ratings[np.where(kva*1.1 < ratings)[0][skip]]
  except IndexError:
    # no more ratings
    return -1

def timetuple2sec(t:list[int]) -> int:
  """Convert time tuple/list with (hr, sec) into a seconds value"""
  if len(t) != 2:
    raise ValueError("Time tuple/list must have 2 elements")
  return t[0]*3600 + t[1]

def sec2timetuple(s:int) -> list[int]:
  """convert an integer number of seconds into a list with (hr, sec)"""
  hr, sec = divmod(s, 3600)
  return [hr, sec]

def get_periodending(time_now:list[int], step:int) -> list[int]:
  """return the end of the period.
  Example, if time is [0,0] (hr, sec) and step is 1hr is function returns [1,0]
  """
  return sec2timetuple(timetuple2sec(time_now) + step)

class HCA:
  def __init__(self, inputs:Union[str,dict], logger_heading=None, 
               reload=False, reload_filemode="a", print_config=False,
               print_parsed_graph=False, reload_start_dss=True):
    if reload:
      self.load(inputs, filemode=reload_filemode, reload_heading=logger_heading, start_dss=reload_start_dss)
      return
    
    if isinstance(inputs, str) or isinstance(inputs, dict):
      # convert to dictionary
      inputs = load_config(inputs)
    if inputs["hca_method"] not in hca_options:
      raise ValueError(f"hca_method must be one of: {hca_options.keys()}")
    self.inputs = copy.deepcopy(inputs)
    self.method = inputs["hca_method"]
    self.change_lines = inputs["change_lines_init"].copy()
    self.change_lines_noprint = []
    self.change_lines_history = []
    self.upgrade_change_lines = []
    self.presolve_edits = []
    self.dss_reset = False
    self.solvetime = inputs["start_time"].copy() #start time for sequence mode in [hr, sec]
    self.endtime = timetuple2sec(inputs["end_time"]) # end time for sequence mode in seconds
    self.timer = ProcessTime()

    self.logger_init(logger_heading)
    
    if print_config:
      self.print_config()

    ## establish a random seed for reproducibility
    # generate a 32bit seed based specified seed OR the choice of feeder
    s = inputs["seed"] if inputs["seed"] else inputs["choice"]
    seed = int.from_bytes(hashlib.sha256(f'{s}'.encode()).digest()[:4], 'little')
    # random.seed(hash(inputs["choice"]))
    self.random_state = np.random.RandomState(seed)

    ## load networkx graph
    self.load_graph()

    self.logger.info('\nLoaded Feeder Model {:s}'.format(self.inputs["choice"]))
    if print_parsed_graph:
      self.print_parsed_graph()

    ## get regulator shapes (if any). Used for sequence method
    if self.inputs["reg_control"]["regulator_shape"]:
      self.reg_shape = {}
      for reg, f in self.inputs["reg_control"]["regulator_shape"].items():
        self.reg_shape[reg] = read_regulator_shape(f)
    else:
      self.reg_shape = None

    if self.inputs["storage_control"]["storage_shape"]:
      self.storage_shape = self.inputs["storage_control"]["storage_shape"].copy()
    else:
      self.storage_shape = None

    ## initialize dss model
    self.dss = i2x.initialize_opendss(printf=self.logger.debug, **self.inputs)
    self.update_basekv()

    ## create a set of voltage monitors throughout the feeder
    self.voltage_monitor(self.inputs["monitors"]["volt_monitor_method"])

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

    ## upgrades are keys by object typ -> object name -> cnt (step through HCA process) -> object specifics
    ###  lines: 
    self.data["upgrades"] = {} #{"line": {}, "transformer": {}}
    
    self.metrics = HCAMetrics(**inputs["metrics"], logger=self.logger)

  def logger_init(self, logger_heading):
    self.logger = Logger(self.inputs["hca_log"]["logname"], 
                         level=self.inputs["hca_log"]["loglevel"], 
                         format=self.inputs["hca_log"]["format"])
    
    if self.inputs["hca_log"]["logtofile"]:
      self.logger.set_logfile(mode=self.inputs["hca_log"]["logtofilemode"],
                              path=self.inputs["hca_log"]["logpath"])

    if logger_heading is not None:
      self.logger.info(logger_heading)

  def save(self, filename):
    """Save the HCA for later re-instantiation vie load
    filename is a pickle file to save, if it is None then the 
    bytes representation of pickle.dumps is retured
    """
    out = {}
    skip = ["logger", "random_state", "dss", "metrics", "lastres", "timer"]
    for k, v in self.__dict__.items():
      if k in skip:
        continue
      else:
        out[k] = copy.deepcopy(v)
    
    out["state"] = self.random_state.get_state()
    out["metrics_baseres"] = copy.deepcopy(self.metrics.base.res)
    out["lastres"] = {k: copy.deepcopy(v) for k, v in self.lastres.items() if k != "dss"}
    # out["G"] = json.dumps(self.G, default=nx.node_link_data)

    if filename is None:
      return pickle.dumps(out)
    else:
      with open(filename, "wb") as f:
        pickle.dump(out, f)
  
  def load(self, filename, filemode=None, reload_heading=None, start_dss=True):
    """Load a saved state of the HCA.
    filename should be:
      - a pickle file or 
      - the bytes representation from pickle.dumps or
      - the dictionary from calling pickle.loads(...)
    """
    
    if not isinstance(filename, str):
      if isinstance(filename, dict):
        tmp = copy.deepcopy(filename)
      else:
        tmp = pickle.loads(filename)
    else:
      with open(filename, "rb") as f:
        tmp = pickle.load(f)

    skip = ["state"]    
    for k, v in tmp.items():
      if k not in skip:
        setattr(self, k, v)

    # self.G = nx.node_link_graph(tmp["G"], directed=True)

    if filemode is not None:
      # make it possible to append to file
      self.inputs["hca_log"]["logtofilemode"] = filemode
    self.logger_init(reload_heading)

    self.metrics = HCAMetrics(**self.inputs["metrics"], logger=self.logger)
    self.metrics.set_base(tmp["metrics_baseres"])

    if start_dss:
      self.reset_dss(clear_changes=False)

    self.random_state = np.random.RandomState()
    self.random_state.set_state(tmp["state"])
    self.timer = ProcessTime()

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
  
  def update_upgrades(self, typ:str, name:str, vals:dict, cnt=None):
    "update the upgrades storage values"
    
    if cnt is None:
      cnt = self.cnt
    if typ not in ["line", "transformer", "transformer_tap", "regulator_vreg"]:
      raise ValueError("Upgrade type must be in ['line', 'transformer']")
    
    if typ not in self.data["upgrades"]:
      self.data["upgrades"][typ] = {}
    name = name.lower()
    if name not in self.data["upgrades"][typ]:
      self.data["upgrades"][typ][name] = {}
    self.data["upgrades"][typ][name][cnt] = copy.deepcopy(vals)
  
  def set_active_bus(self, bus, recalculate=False):
    self.logger.info(f"Setting bus {bus} as active bus")
    self.active_bus = bus
    self.active_bus_kv = self.G.nodes[bus]["ndata"]["nomkv"]
    if not recalculate:
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

  def reset_dss(self, clear_changes=True):
    """recompile feeder and load changes from history"""
    # key = "tmp" if tmp else "nontmp"
    if clear_changes:
      self.clear_changelines()
    self.dss = i2x.initialize_opendss(**self.inputs)
    for l in self.change_lines_history:
      self.dss.text(l)

  def save_circuit(self, filename=None, dirname=None):
    filearg = ''
    dirarg = ''
    if filename is not None:
      filearg = 'file={:s}'.format(filename)
    if dirname is not None:
      dirarg = 'dir={:s}'.format(dirname)
    self.dss.text('save circuit {:s} {:s}'.format (filearg, dirarg))
#    self.dss.text('save pvsystem {:s} {:s}'.format (filearg, dirarg))

  def verify_inverter_mode(self, verbose=False):
    """Verify that there is an inverter control object created
    Done by saving the circuit and checking that that InvControl.dss file exists
    """
    dirname = "tmp_dss_save"
    self.save_circuit(dirname=dirname)
    out = os.path.isfile(os.path.join(dirname, "InvControl.dss"))
    if out and verbose:
      with open(os.path.join(dirname, "InvControl.dss")) as f:
        self.logger.info("\nInverter Mode Test:")
        self.logger.info(f.read())
    shutil.rmtree(dirname) # remove temporary directory
    return out

  def clear_changelines(self):
    """clear change lines. Call between successive calls to rundss"""
    self.change_lines_noprint = []
    self.change_lines = []
    self.presolve_edits = [] # Note that these DO NOT get saved!!!

  def replay_resource_addition(self, typ, bus, cnt):
    key = self.resource_key(typ, bus, cnt)
    self.new_capacity(typ, key, bus=bus, **self.data["Sij"][typ][bus][cnt])

  def resource_key(self, typ, bus, cnt, recalculate=False):
    return f"{typ}_{bus}_cnt{cnt}{'_recalc' if recalculate else ''}"
  
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

  def voltage_monitor(self, method):
    """Add voltage monitors throughout the system"""

    def get_elem_and_term(dss:py_dss_interface.DSSDLL, bus):
      dss.circuit.set_active_bus(bus)
      for elem in dss.bus.all_pde_active_bus:
        # loop over the connected elements to this bus to
        dss.circuit.set_active_element(elem)
        # get the number of the terminal that is connected to bus
        term = [s.split(".")[0] for s in dss.cktelement.bus_names].index(bus) + 1
        return elem, term
    if method == 'bfs':
      ## place a monitor at each level of a breadth firs search from source
      depth = 1
      H = isl.get_nondir_tree(self.G)
      source = isl.get_single_source(H)
      while True:
        n = list(nx.descendants_at_distance(H, source, depth))
        n.sort() # for reproducibility
        self.logger.debug(f"voltage_monitor: depth {depth}\n\t buses: {n}")
        if not n:
            break
        
        ns = n[self.random_state.randint(0, len(n))]
        elem, term = get_elem_and_term(self.dss, ns)
        # elem = self.G.nodes[ns]["ndata"]["shunts"][0] # select the first shunt
        self.change_lines_noprint.append(f"new monitor.{ns}_volt_vi element={elem} terminal={term} mode=96") # add a voltage monitor
        depth += 1
    elif method == 'all':
      for ns in self.G.nodes():
        elem, term = get_elem_and_term(self.dss, ns)
        self.change_lines_noprint.append(f"new monitor.{ns}_volt_vi element={elem} terminal={term} mode=96") # add a voltage monitor
    elif method == 'none':
      # don't add any voltage monitors
      pass
    else:
      raise ValueError(f"Voltage Monitor addition method {method} is not implemented, options are: 'bfs', 'all', 'none'.")

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

  def remove_der(self, key, typ, bus, kva, kw, kwh=0):
    if kw==0:
      # this could be the case where there is no hc, but we still want to remove the last bit added
      # during the hc_bisection. To do this, get the Sij stored at this bus:
      # option 1: something exists -> set kw, kva to return to this value
      # option 2: nothing exists -> set kw, kva to zero out
      typmap = {"solar": "pv", "storage": "bat", "generator": "der"}
      graph_keys = {"solar": "pv", "storage": "bat", "generator": "gen"}
      Sij, cnt = self.get_data("Sij", typmap[typ], bus)
      if Sij is None:
        Sij = {"kw": 0, "kva": 0}
      
      kw = self.G.nodes[bus]["ndata"][f"{graph_keys[typ]}kw"] - Sij["kw"]
      kva = self.G.nodes[bus]["ndata"][f"{graph_keys[typ]}kva"] - Sij["kva"]
      
    row = {"type": typ, "bus": bus, "kva": kva, "kw": kw, "kwh": kwh}
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
      self.G.nodes[row["bus"]]["ndata"]["pvkva"] -= row["kva"]
      self.G.nodes[row["bus"]]["ndata"]["pvkw"] -= row["kw"]
    elif row['type'] == 'storage':
      self.change_lines.append('edit storage.{:s} enabled=no'.format(key))
      self.G.nodes[row["bus"]]["ndata"]["batkva"] -= row["kva"]
      self.G.nodes[row["bus"]]["ndata"]["batkw"] -= row["kw"]
      self.G.nodes[row["bus"]]["ndata"]["batkwh"] -= row["kwh"]
    elif row['type'] == 'generator':
      self.change_lines.append('edit generator.{:s} enabled=no'.format(key))
      self.G.nodes[row["bus"]]["ndata"]["genkva"] -= row["kva"]
      self.G.nodes[row["bus"]]["ndata"]["genkw"] -= row["kw"]
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
  
  def disable_regulators(self, reglist=[]):
    if not reglist:
      self.change_lines.append("batchedit regcontrol..* enabled=no")
    else:
      for r in reglist:
        self.change_lines.append(f"edit regcontrol.{r} enabled=no")

  def apply_regulator_shape(self):
    """if regulator shapes are present, these are used to determine the
     initial tap setting of those regulators
     The regulator shape is indexed on (hr,sec) and the current solution time
     is used to pick out a value.
     Since the regulator shape shows the HOUR ENDING. we index for one step in the future.
    """
    if self.reg_shape is None:
      # no regulator shapes
      return
    for k, v in  self.reg_shape.items():
      tmp = v.loc[tuple(get_periodending(self.solvetime, self.inputs["stepsize"]))]
      cmd = f"edit transformer.{k} wdg={tmp.wdg} tap={tmp.tap_pu}"
      self.presolve_edits.append(cmd)

  def apply_storage_shape(self):
    """if storage shapes were defined (for storage that is replaced by a load)
    then these are added to presolve_edits here.
    NOTE: shape should have been defined as a load shape (probably in change_lines 
    passed in to the object on initialization)
    """ 
    if self.storage_shape is None:
      # no storage shapes
      return
    for k, v in self.storage_shape.items():
      # set the load shape. NOTE assumption is that this is a load model!!!
      cmd = f"edit load.{k} daily={v} yearly={v}"
      self.presolve_edits.append(cmd)

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
      self.G.nodes[bus]["ndata"]["pvkva"] += kva
      self.G.nodes[bus]["ndata"]["pvkw"] += kw
      self.G.nodes[bus]["ndata"]["nomkv"] = kv
      self.G.nodes[bus]["ndata"]["shunts"].insert(0, f"pvsystem.{key}") #prepend to shunt list (make sure this is the first element found)

  def append_large_storage(self, key):
    self._append_large_storage(key, **self.inputs["explicit_storage"][key])

  def _append_large_storage (self, key, bus, kv, kva, kw, kwh):
    self.change_lines.append('new storage.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f} kwhrated={:.3f} kwhstored={:.3f}'.format(key, bus, kv, kva, kw, kwh, 0.5*kwh))
    if not self.existing_resource_check(f"storage.{key}", bus, "batkva", kva):
      self.G.nodes[bus]["nclass"] = 'storage' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
      self.G.nodes[bus]["ndata"]["batkva"] += kva
      self.G.nodes[bus]["ndata"]["batkw"] += kw
      self.G.nodes[bus]["ndata"]["batkwh"] += kwh
      self.G.nodes[bus]["ndata"]["nomkv"] = kv
      self.G.nodes[bus]["ndata"]["shunts"].insert(0, f"storage.{key}") #prepend to shunt list (make sure this is the first element found)

  def append_large_generator(self, key):
    self._append_large_generator(self, key, **self.inputs["explicit_generator"][key])
  def _append_large_generator (self, key, bus, kv, kva, kw):
    self.change_lines.append('new generator.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f}'.format(key, bus, kv, kva, kw))
    if not self.existing_resource_check(f"generator.{key}", bus, "genkva", kva):
      self.G.nodes[bus]["nclass"] = 'generator' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
      self.G.nodes[bus]["ndata"]["genkva"] += kva
      self.G.nodes[bus]["ndata"]["genkw"] += kw
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
    if self.inputs["reg_control"]["disable_all"]:
      self.disable_regulators()
    elif self.inputs["reg_control"]["disable_list"]:
      self.disable_regulators(reglist=self.inputs["reg_control"]["disable_list"])

    
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

  def step_solvetime(self, stepcnt=True):
    """increment the solution time by the stepsize (for sequence method)
    time is a tuple with (hr, sec)
    If stepcnt is True the internal counter self.cnt is incremented by 1
    """
    tmp = timetuple2sec(self.solvetime) ## convert to seconds
    tmp += self.inputs["stepsize"]      ## increment
    self.solvetime = sec2timetuple(tmp) ## convert back to time tuple
    if stepcnt:
      self.cnt += 1

  def is_endtime(self):
    """Returns True when the solvetime has reached/passed the endtime, 
    otherwise returns False"""

    if timetuple2sec(self.solvetime) < self.endtime:
      return False
    else:
      return True

  def set_endtime(self, t:list[int]):
    """set the endtime to t (hr, sec)"""

    self.endtime = timetuple2sec(t)

  def set_solvetime(self, t:list[int]):
    """set the solvetime to t (hr, sec)"""
    self.solvetime = t

  def rundss(self,solvetime:list[int]=None):
    if solvetime is None:
      if self.inputs["hca_method"] == "sequence":
        ## for sequence method, make sure that the right time instance is simulated
        solvetime = self.solvetime
    ## add commands to set regulators (does nothing if self.reg_shape is None)
    self.apply_regulator_shape()
    ## add commands to have storage (modeled as load) follow a shape different from other load
    self.apply_storage_shape()
    pwd = os.getcwd()
    self.lastres = i2x.run_opendss(**{**{"change_lines": self.change_lines + self.change_lines_noprint + self.upgrade_change_lines, 
                                         "dss": self.dss, "solvetime":solvetime, "presolve_edits": self.presolve_edits,
                                         "demandinterval": True, "printf": self.logger.debug}, 
                                         **self.inputs} )  
    if self.lastres["converged"]:
      self.lastres["compflows"] = isl.all_island_flows(self.comp2rec, self.lastres["recdict"])
      os.chdir(pwd)
      self.read_di_outputs()

  def summary_outputs(self):
    summary_outputs(self.lastres, self.pvbases, print=self.logger.info)

  def read_di_outputs(self):
    path = os.path.join(self.dss.dssinterface.datapath, self.dss.circuit.name, "DI_yr_0")
    ### Thermal overloads
    dtypes = {(float, int): ["NormalAmps", "EmergAmps", "%Normal", "%Emerg", "kVBase", "I1(A)", "I2(A)", "I3(A)"]}
    df, cols, err = self._load_di(path, "DI_Overloads_1.CSV", dtypes=dtypes)
    cols.remove("Hour")
    cols.remove("Element")
    ### aggregate all columns based on max except for "%Normal" where we count the number of violoations
    ### for %Normal we then multiply by dt to get the violation time over normal.
    agg_map = {c: "max" for c in cols}
    agg_map["hrs_above_normal"] = "sum"
    cols.append("hrs_above_normal")
    df["hrs_above_normal"] = df["%Normal"] > 100
    self.lastres["di_overloads"] = df.groupby("Element").agg(agg_map).loc[:, cols]
    self.lastres["di_overloads"]["hrs_above_normal"] *= self.inputs["stepsize"]/3600 # convert count to hrs
    self.lastres["di_overloads"].index = self.lastres["di_overloads"].index.str.strip(' "') # remove spaces and quotes
    if err:
      self.lastres["converged"] = False
    ### Voltage violations
    dtypes = {int: ["Undervoltages", "Overvoltage", "LVUndervoltages", "LVOvervoltage"],
              float: ["MinVoltage","MaxVoltage", "MinLVVoltage", "MaxLVVoltage"]}
    df, cols, err = self._load_di(path, "DI_VoltExceptions_1.CSV", dtypes=dtypes)
    self.lastres["di_voltexceptions"] = df.set_index("Hour")
    if err:
      self.lastres["converged"] = False
    ### Totals (just use to keep finer grain track of EEN and UE for now)
    dtypes = {(float, int): ["LoadEEN", "LoadUE"]}
    df, cols, err = self._load_di(path, "DI_Totals_1.CSV", dtypes=dtypes)
    cols = ["LoadEEN", "LoadUE", "kWh", "kvarh", "MaxkW", "MaxkVA"]
    self.lastres["di_totals"] = df.set_index("Time").loc[:, cols]
    if err:
      self.lastres["converged"] = False

  def calc_total_een_ue(self, ditotals:pd.DataFrame):
    """perform integration of EEN and UE in the totals result"""
    return ditotals.transpose().dot(np.diff(np.insert(ditotals.index, 0, [0])))

  def _load_di(self, path:str, name:str, dtypes=None) -> tuple[pd.DataFrame, list]:
    df = pd.read_csv(os.path.join(path, name))
    cols = [c.replace('"','').replace(' ','') for c in df.columns] # some cleanup
    df.columns = cols
    
    err = False
    if (not df.empty) and (dtypes is not None):
      ## check dtype. Prolems can happen this can happen if there are INFs or NANs
      for typ, typcols in dtypes.items():
        dfcols = df.select_dtypes(typ)
        for col in typcols:
          if col not in dfcols:
            self.logger.warn(f"_load_di {name}: column {col} is not of type {typ} but of type {df[col].dtype}")
            if isinstance(typ, tuple):
              df[col] = df[col].str.strip().astype(typ[0])
            else:
              df[col] = df[col].str.strip().astype(typ)
            err = True
    return df, cols, err
  
  def sample_capacity(self, typ, kwcap=None):
    """sample unit capacity based on typ"""
    while True:
      if typ == "pv":
        out = self._sample_pv(kwcap=kwcap)
      elif typ == "bat":
        out = self._sample_bat(kwcap=kwcap)
      elif typ == 'der':
        out = self._sample_der(kwcap=kwcap)
      else:
        raise ValueError("Can only handle pv, bat, and der (gen) currently")
      if (kwcap is None) or (out["kw"] <= kwcap):
        break
    return out

  def _sample_pv(self, kwcap=None):
    """return a PV system with capacity between 50 kW and 1000 kW and pf 0.8"""
    if (kwcap is not None) and (kwcap < 50):
      kw = kwcap
    else:
      kw = float(self.random_state.randint(50, 1001))
    kva = kw/0.8
    return {"kw": kw, "kva": kva}
  
  def _sample_bat(self, kwcap=None):
    """return a 2 or 4 hour battery with capacity between 50 kW and 1000 kW and kVA"""
    if (kwcap is not None) and (kwcap < 50):
      kw = kwcap
    else:
      kw = float(self.random_state.randint(50, 1001))
    kva = kw
    kwh = [2,4][self.random_state.randint(0,2)]
    # kwh = random.choice([2,4])*kw
    return {"kw": kw, "kva": kva, "kwh": kwh}

  def _sample_der(self, kwcap=None):
    """TODO: for now just same as PV"""
    return self._sample_pv(kwcap=kwcap)

  def new_capacity(self, typ, key, bus=None, **kwargs):
    """create new capacity during hca round"""
    if bus is None:
      bus = self.active_bus
    kv = self.G.nodes[bus]["ndata"]["nomkv"]
    if typ == "pv":
      self._append_large_pv(key, bus, kv, **kwargs)
      if self.method == "sequence":
        ### for sequence method pv is used as a general representation of a generator
        # make
        self.presolve_edits.append(f"edit pvsystem.{key} daily=flat yearly=flat duty=flat")
        ## TODO: make it possible to have different controls for hca additions vs exisiting
        # if self.inputs["hca_control_mode"] is not None:
        #   if self.inputs["hca_control_mode"] == "CONSTANT_PF":
        #     self.presolve_edits.append(f'edit pvsystem.{key} pf={self.inputs["hca_control_pf"]}')
        #   else:
        #     pass
        #   #TODO

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

  def get_data(self, key, typ, bus=None, cnt=None):
    """Retrieve the hosting capacity, Sij, or eval stored for the given bus for the given type.
    If no iteration counter is given the process works itself backwards from the
    current count until a viable index is found.
    """
    if key not in ["Sij", "hc", "eval", "upgrades"]:
      raise ValueError("key must be Sij, hc, or eval")
    if typ not in ["pv", "bat", "der", "line", "transformer", "transformer_tap", "regulator_vreg"]:
      raise ValueError("Currently Only differentiating on pv, bat, der, line, transformer, transformer_tap, regulator_vreg")
    
    if bus is None:
      ## iterate over all buses in this key/type
      out = {}
      for b in self.data[key][typ].keys():
        data, cntout = self.get_data(key,typ,b,cnt=cnt)
        if data is not None:
          out[b] = {**data, "cnt": cntout}
      return pd.DataFrame.from_dict(out, orient="index")
    else:
      if cnt is not None:
        try:
          return self.data[key][typ][bus][cnt], cnt
        except KeyError:
          return None, cnt
      else:
        cnt = self.cnt
        while cnt >= 0:
          data, cnt =  self.get_data(key, typ, bus, cnt)
          if data is None:
            cnt -= 1
          else:
            return data, cnt
        return None, cnt #if we're here then no data was found, cnt should be -1
    
  def get_hc(self, typ, bus=None, cnt=None, latest=False):
    """Retrieve the hosting capacity stored for the given bus for the given type
    if no iteration counter is given the process works itself backwards from the
    current count until a viable index is found.

    For the sequence method, a dataframe is returned of hosting capacity at all counts
    i.e. time instances. using latest=True forces the other behavior.
    """
    if (bus is not None) and (self.method == "sequence") and (not latest):
      ## return a dataframe of all time indices for the bus
      return pd.DataFrame.from_dict(self.data["hc"][typ][bus], orient="index")
    else:
      return self.get_data("hc", typ, bus=bus, cnt=cnt)
  
  def remove_hca_resource(self, typ, bus=None, cnt=None, recalculate=False):
    """utility function for remove a resource added via hca_round.
    The main purpose is to make sure the graph gets updated as necessary.
    If bus and cnt are none it is assumed that the current count and active bus 
    last visited bus is intended
    """
    typmap = {"pv": "solar", "bat": "storage", "der": "generator"}
    if cnt is None:
      cnt = self.cnt
    if bus is None:
      if self.active_bus is None:
        bus = self.visited_buses[-1]
      else:
        bus = self.active_bus

    # get the key used for the resource
    key = self.resource_key(typ, bus, cnt, recalculate=recalculate)
    Sij, cnt = self.get_data("Sij", typ, bus, cnt)

    self.remove_der(key, typmap[typ], bus, **Sij)

    self.parse_graph() #update graph dictionaries

  def undo_hca_round(self, typ, bus, cnt):
    """undo an hca round"""
    ### remove the resource
    self.remove_hca_resource(typ, bus, cnt)
    
    ### remove the total statistics
    self.data["Stotal"].pop(cnt)

    ### remove results from self.data
    for k in ["Sij", "hc", "eval"]:
      self.data[k][typ][bus].pop(cnt)
      # check if the bus has no data left (common):
      if not self.data[k][typ][bus]:
        self.data[k][typ].pop(bus)

    ### remove from visited buses list
    # verify that the bus is really at the cnt index
    if self.visited_buses[cnt-1] == bus:
      self.visited_buses.pop(cnt-1)

    ### reset open dss
    ### Removes the resource addition as long as it was still
    ### in change lines, i.e. save_state was not called.
    self.reset_dss()


  def hca_round(self, typ, bus=None, Sij=None, 
                allow_violations=False, hciter=True, recalculate=False,
                set_sij_to_hc=False, unset_active_bus=True,
                bnd_strategy=None):
    """perform a single round of hca"""
    
    self.timer.start()
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
    if not recalculate:
      self.cnt +=1
    self.logger.info(f"\n========= HCA Round {self.cnt} {f'dss time: {self.solvetime}' if self.method=='sequence' else ''} ({typ}){' recalculating' if recalculate else ''}=================")
  
    #### Step 1: select a bus. Viable options (for now) are:
    # * graph_dirs["bus3phase"]: 3phase buses with nothing on them
    # * any bus already considered in a previous round (since the capacity added may not have been the limit)
    # * **exclude** buses that have zero hosting capacity
    if bus is None:
      buslist = [b for b in list(self.graph_dirs["bus3phase"]) + self.visited_buses if b not in self.exauhsted_buses[typ]]
      
      self.set_active_bus(self.sample_buslist(buslist))
    else:
      self.set_active_bus(bus, recalculate=recalculate)

    #### Step 2: Select new capacity, 
    ## there are two options:
    ## 1. this bus an evaluated hc -> use this value as the starting point
    ## 2. this has not been visited -> sample a capacity (add to existing (0 or otherwise))
    if Sij is not None:
      self.logger.info(f"Specified capacity: {Sij}")
    else:
      hc, hc_cnt = self.get_hc(typ, self.active_bus, latest=True)
      if (hc is not None) and (hc["kw"] > 0):
        kwcap = hc["kw"]
      else:
        kwcap = None
      Sij = self.sample_capacity(typ, kwcap=kwcap)
      self.logger.debug(f"\tsampled {Sij}")
      if set_sij_to_hc:
        keyexist = self.get_classkey_from_node(nclass[typ], self.active_bus)
        if keyexist is not None: 
          ## Option 1: check if bus already has resource of this type
          self.logger.debug(f"\tFound resource {keyexist}, at bus {bus}")
          hc, hc_cnt = self.get_hc(typ, self.active_bus, latest=True)
          if (hc is not None) and (hc["kw"] > 0):
            # use the hc value
            self.logger.debug(f"\tLast hc info from round {hc_cnt}: {hc}")
            Sij = hc
          else:
            self.logger.debug(f"\tNo hc available, using sampled value")

    ### Create resource     
    key = self.resource_key(typ, self.active_bus, self.cnt, recalculate=recalculate) #f"{typ}-init-cnt{self.cnt}"
    if (not recalculate) or (self.logger.getlevel() == "DEBUG"):
      self.logger.info(f"Creating new {typ} resource {key} with S = {Sij}")
    self.new_capacity(typ, key, **Sij)
    Sijin = copy.deepcopy(Sij)
    ### update graph structure and log changes
    self.parse_graph()
    for ln in self.change_lines:
      self.logger.debug (f' {ln}')

    ### Step 3: Solve
    self.rundss()
    if self.lastres["converged"]:
      # raise ValueError("Open DSS Run did not converge")

      ### Step 4: evaluate
      # evaluate the run with following options:
      # 1. no violations: fix capaity Sij, increment until violations occure to determine hc
      # 2. violations: decrease capacity until no violations. set hc=0 (mark bus as exauhsted)
      self.metrics.load_res(self.lastres)
      self.metrics.calc_metrics()
    else:
      self.logger.warn(f"hca_round: DSS appears to have not converged")
    if self.lastres["converged"] and (self.metrics.violation_count == 0):
      # no violations
      if (not recalculate) or (self.logger.getlevel() == "DEBUG"):
        self.logger.info(f"No violations with capacity {Sij}.")
      if not recalculate:
        self.update_data("Sij", typ, Sij)  # save installed capacity
      if hciter:
        self.logger.info("Iterating to find HC.")
        Sijlim = self.hc_bisection(typ, key, Sijin, Sij, None, 
                                   bnd_strategy=bnd_strategy) # find limit via bisection search
        if recalculate:
          hc = {k: Sijlim[k] for k in ["kw", "kva"]}
        else:
          hc = {k: Sijlim[k] - Sij[k] for k in ["kw", "kva"]}
        hc["violations"] = self.metrics.last_violation_list
        self.update_data("hc", typ, hc)
      self.update_data("eval", typ, self.metrics.eval)
    else:
      # violations: decrease capacity to find limit (or non-convergence)
      if (not recalculate) or (self.logger.getlevel() == "DEBUG"):
        self.logger.info(f"Violations with capacity {Sij} (allow_violations is {allow_violations}).")
      if self.lastres["converged"]:
        if (not recalculate) or (self.logger.getlevel() == "DEBUG"):
          self.logger.info(f"\t{','.join(self.metrics.get_violation_list())}")
        self.logger.debug(f"\t\tviolations: {self.metrics.violation}")
      if allow_violations:
        self.update_data("Sij", typ, Sij)
        self.update_data("eval", typ, self.metrics.eval)
        hc_violations = self.metrics.get_violation_list()
      if hciter:
        self.logger.info("Iterating to find Limit.")
        Sijlim = self.hc_bisection(typ, key, Sijin, None, Sij,
                                    bnd_strategy=bnd_strategy)
        if Sijlim["kw"] == 0: 
          # no capacity at this bus (not just no *additional*, none at all)
          # remove the object from the graph
          self.logger.info(f"\tNo capacity at bus {self.active_bus}. Disabling resource {key}.")
          # self.remove_der(key, typmap[typ], self.active_bus) # dss command doesn't really matter, but this removes it from graph as well
          # self.reset_dss() # reset state to last good solution
        if recalculate:
          hc = copy.deepcopy(Sijlim)
        else:
          hc = {k: 0 for k in ["kw", "kva"]}
        if allow_violations:
          hc["violations"] = hc_violations
        else:
          hc["violations"] = self.metrics.last_violation_list
        self.update_data("hc", typ, hc)
        if not allow_violations:
          Sij = copy.deepcopy(Sijlim)
          if not recalculate:
            self.update_data("Sij", typ, Sij) # update with intalled capacity
          self.update_data("eval", typ, self.metrics.eval)
      # mark bus as exauhsted
      if not recalculate:
        self.exauhsted_buses[typ].append(self.active_bus)

    ### Step 5: final run with the actual capacity
    self.logger.info(f"*******Results for bus {self.active_bus} ({typ}) in {self.timer.stop(print=True)}")
    if not recalculate:
      # when recalculating the selected capacity is not relevant, so don't report
      self.logger.info(f"Sij = {Sij}")
    self.logger.info(f"hc = {hc}")
    if hciter:
      self.remove_der(key, typmap[typ], self.active_bus, **Sijlim) # dss command doesn't really matter, but this removes it from graph as well
    else:
      self.remove_der(key, typmap[typ], self.active_bus, **Sijin) # dss command doesn't really matter, but this removes it from graph as well
    self.reset_dss() # reset state to last good solution
    if (Sij["kw"] > 0) and (not recalculate):
      self.new_capacity(typ, key, **Sij)
    ### update graph structure and log changes
    self.parse_graph()
    for ln in self.change_lines:
      self.logger.debug (f' {ln}')
    self.rundss()
    if not self.lastres["converged"]: #don't allow non-convergence here
      raise ValueError("Open DSS Run did not converge")
    
    if allow_violations and hciter and (Sijlim["kw"] < Sij["kw"]):
      # violations are allowed an we installed capacity that will create some
      # recalculate metrics
      self.metrics.load_res(self.lastres)
      self.metrics.calc_metrics()
    elif recalculate:
      # if we are just recalculating at a bus, make sure to update results
      self.metrics.load_res(self.lastres)
      self.metrics.calc_metrics()

    ### cleanup
    if unset_active_bus:
      ## allow keeping bus active (useful for first iteration of sequence mode)
      self.unset_active_bus()
    self.collect_stats()

  def hc_bisection(self, typ, key, Sijin, Sij1=None, Sij2=None, kwtol=5, kwmin=30,
                   bnd_strategy=None):
    """
    perform search for hc value, default is bisection (bnd_strategy=("mult", 2))
    bnd_strategy is a tuple.
      elem[0] = "mult" -> multiply/divide by a factor > 1
                "add"  -> add/subtract factor > 0
      elem[1] = factor to be multiplied or added
    """
    if bnd_strategy is None:
      bnd_strategy = ("mult", 2)
    if bnd_strategy[0] not in ["mult", "add"]:
      raise ValueError(f"bnd_strategy elem[0] must be in ['mult', 'add'] but {bnd_strategy[0]} given")
    if bnd_strategy[0] == "mult":
      if bnd_strategy[1] <= 1:
        raise ValueError(f"with bnd_strategy[0] = 'mult' bnd_strategy[1] must be > 1, {bnd_strategy[1]} given.")
    elif bnd_strategy[0] == "add":
        if bnd_strategy[1] <= 0:
          raise ValueError(f"with bnd_strategy[0] = 'add' bnd_strategy[1] must be > 0, {bnd_strategy[1]} given.")
        
    typmap = {"pv": "solar", "bat": "storage", "der": "generator"}
    #prep for new run
    self.remove_der(key, typmap[typ], self.active_bus, **Sijin) # dss command doesn't really matter, but this removes it from graph as well
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
      # unknown upperbound
      if bnd_strategy[0] == "mult":
        # double (default) lower bound
        Sijnew = {k: bnd_strategy[1]*v for k, v in Sij1.items()}
      elif bnd_strategy[0] == "add":
        # add a constant to kw, keep factor pf constant
        Sijnew = {"kw": Sij1["kw"] + bnd_strategy[1]}
        factor = Sijnew["kw"]/Sij1["kw"]
        for k in Sij1.keys():
          if k != "kw":
            Sijnew[k] = Sij1[k]*factor # apply to other properties proportionally 
    elif Sij1 is None:
      # unknown lower bound
      if bnd_strategy[0] == "mult":
        # halve (default) the upper bound
        Sijnew = {k: v/bnd_strategy[0] for k, v in Sij2.items()}
      elif bnd_strategy[0] == "add":
        # subtract a constant to kw, keep factor pf constant
        Sijnew = {"kw": Sij2["kw"] - bnd_strategy[1]}
        factor = Sijnew["kw"]/Sij2["kw"]
        for k in Sij2.keys():
          if k != "kw":
            Sijnew[k] = Sij2[k]*factor # apply to other properties proportionally 
    
    self.new_capacity(typ, key, **Sijnew) #add the new capacity

    ### update graph structure and log changes
    self.parse_graph()
    for ln in self.change_lines:
      self.logger.debug (f' {ln}')

    ### Solve
    self.rundss()
    if self.lastres["converged"]:
      # raise ValueError("Open DSS Run did not converge")
    
      self.metrics.load_res(self.lastres)
      self.metrics.calc_metrics()
    else:
      self.logger.warn(f"hc_bisection: DSS appears to have not converged")
    if self.lastres["converged"] and (self.metrics.violation_count == 0):
      if self.inputs["hca_log"]["print_hca_iter"]:
        self.logger.info(f"\tNo violations with capacity {Sijnew}. Iterating to find HC")
      if Sij2 is None:
        # still uknown upper bound
        return self.hc_bisection(typ, key, Sijnew, Sijnew, None,
                                 kwtol=kwtol, kwmin=kwmin, bnd_strategy=bnd_strategy)
      elif Sij2["kw"] - Sijnew["kw"] < kwtol:
        # End criterion: no violations and search band within tolerance
        if Sijnew ["kw"] < kwmin:
          # if capacity is below a minimum threshold set to 0
          Sijnew = {k: 0 for k in Sijnew.keys()}
        return Sijnew
      else:
        # recurse and increase
        return self.hc_bisection(typ, key, Sijnew, Sijnew, Sij2,
                                 kwtol=kwtol, kwmin=kwmin, bnd_strategy=bnd_strategy)
    else:
      if self.inputs["hca_log"]["print_hca_iter"]:
        self.logger.info(f"\tViolations with capacity {Sijnew}. Iterating to find Limit.")
      if self.lastres["converged"]:
        if self.inputs["hca_log"]["print_hca_iter"]:
          self.logger.info(f"\t{','.join(self.metrics.get_violation_list())}")
          self.logger.debug(f"\t\tviolations: {self.metrics.violation}")
      if Sijnew["kw"] < kwmin:
        # End criterion: upperbound is below minimum threshold set to 0 and exit
        return {k: 0 for k in Sijnew.keys()}
      elif Sij1 is None:
        # still unkonwn lower bound
        return self.hc_bisection(typ, key, Sijnew, None, Sijnew, 
                                 kwtol=kwtol, kwmin=kwmin, bnd_strategy=bnd_strategy)
      else:
        # recurse and decrease
        return self.hc_bisection(typ, key, Sijnew, Sij1, Sijnew, 
                                 kwtol=kwtol, kwmin=kwmin, bnd_strategy=bnd_strategy)
  
  def runbase(self, verbose=0, skipadditions=False):
    """runs an initial version of the feeder to establish a baseline.
    Metrics, for example will be evaluated w.r.t to this baseline as opposed
    to just the hard limits
    if skipadditions is true the deterministic changes and added rooftop pv
    will not be considered (useful for sequence mode post the very first run)
    """
    ###########################################################################
    ##### Initialization
    ###########################################################################
    if not skipadditions:
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

  def commit_upgrades(self):
    """ move upgrades form their own change line list to the general change_lines.
    The general list gets saved when called save_dss_state
    """
    self.change_lines.extend(copy.deepcopy(self.upgrade_change_lines))
    self.clear_upgrades()

  def clear_upgrades(self):
    """Empty the upgrade changle lines list"""
    self.upgrade_change_lines = []

  def copy_upgrades(self, obj:HCA):
    """copy upgrade data from another HCA object.
    The upgrades are placed on the **current** object cnt
    IMPORTANT: this will not work if an object has been upgraded twice!
    """
    ## copy the actual dss commands
    self.upgrade_change_lines.extend(obj.upgrade_change_lines.copy())

    ## copy the upgrade data, altering all cnt keys to self.cnt
    for typ, vals in obj.data["upgrades"].items():
      if typ not in self.data["upgrades"]:
        self.data["upgrades"][typ] = {}
      ## iteration of typ (line, transformer, ...)
      for obj, data in vals.items():
        for cnt, upgrade in data.items():
          self.data["upgrades"][typ].update({obj: {self.cnt: copy.deepcopy(upgrade)}})

  def upgrade_line(self, name, factor=2):
    try:
      brf, brt, brdata = isl.get_branch_elem(self.G, ["eclass", "ename"], ["line", name.lower()])[0]
    except IndexError:
      try:
        # just search by name
        brf, brt, brdata = isl.get_branch_elem(self.G, ["ename"], [name.lower()])[0]
      except IndexError:
        raise IndexError(f"Unable to find line {name} in graph.")
    out = upgrade_line(self.dss, self.upgrade_change_lines, name, factor)
    self.logger.info(f"Upgraded line {name} from {out['old']} A to {out['new']} A")
    out["length"] = brdata["edata"]["length"] # add the original length
    out["length_unit"] = brdata["edata"]["units"] # add units for later cost calculation
    out["cost"] = conductor_cost.get_cost("oh", out["length"], unit=out["length_unit"])
    self.update_upgrades("line", name, out)

  def upgrade_xfrm(self, name):
    
    ### get the transformer data from the graph
    xfrm = None
    for name_tmp in get_parallel_xfrm(self.dss, name):
      try:
        brf, brt, xfrm = isl.get_banch_elem(self.G, ["ename"], [name_tmp.lower()])[0]
        break
      except IndexError:
        pass
    if xfrm is None:
      raise IndexError(f"Unable to find xfrm {name} (or any parallel xfrms) in graph.")
    
    kva_old = get_xfrm_kvas(self.dss, name)[0]
    kva_new = next_xfrm_kva(kva_old, xfrm["edata"]["phases"])
    if kva_new < 0:
      raise ValueError(f"Unable to upgrade transformer {name}. kva_old = {kva_old}")
    out = upgrade_xfrm(self.dss, self.upgrade_change_lines, name, kva_new/kva_old)
    self.logger.info(f"Upgraded xfrm {name} from {out['old']} kVA to {out['new']} kVA")
    self.update_upgrades("transformer", name, out)
  
  def change_xfrm_tap(self, name:str, tapchange:int):
    out = change_xfrm_tap(self.dss, self.upgrade_change_lines, name, tapchange)
    self.logger.info(f"Changed xfrm {name} tap from {out['old']:0.4f} p.u. to {out['new']:0.4f} p.u.")
    out["cost"] = reg_cost.get_cost("settings") # cost is similar to regulator settings change
    self.update_upgrades("transformer_tap", name, out)
  
  def change_regulator_vreg(self, xfrmname:str, vregchange:int):
    out = change_regulator_vreg(self.dss, self.upgrade_change_lines, 
                                xfrmname, vregchange,
                                printf=self.logger.info)
    self.logger.info(f"Changed regulator {xfrmname} regulated voltage from {out['old_pu']:0.4f} p.u. to {out['new_pu']:0.4f} p.u.")
    out["cost"] = reg_cost.get_cost("settings")
    self.update_upgrades("regulator_vreg", xfrmname, out)
class HCAMetrics:
  def __init__(self, limits:dict, comp=None, tolerances=None, 
               include=dict(), exclude=dict(), logger=None):
    self.tests = {
      "voltage": {
      "vmin": self._vmin,
      "vmax": self._vmax,
      "vdiff": self._vdiff
      },
      "thermal": {
      "emerg": self._thermal,
      "norm_hrs": self._norm_hrs,
      },
      "island": {
        "pq": self._island_pq
      } 
    }

    ## select which metrics to use
    if (len(include)) > 0 and (len(exclude) > 0):
      raise ValueError("HCAMetrics: one can specify metrics to include OR metrics to exclude but not both!")
    elif len(include) > 0:
      # only include metrics specified in include dictionary
      out = {}
      self.add_test(include, out)
      self.tests = out
    elif len(exclude) > 0:
      self.exclude_test(exclude)
    if tolerances is None:
      tolerances = {k: 1e-3 for k in self.tests.keys()}

    if logger is not None:
      self.logger = logger
    else:
      self.logger = None
    self.base = None
    self.comp = comp
    self.load_lims(limits)
    self.eval = {}
    self.violation = {}
    self.violation_count = 0
    self.tol=tolerances
    self.last_violation_list = []
  
  def print_metrics(self):
    if self.logger is None:
      printf = print
    else:
      printf = self.logger.info
      
    print_config(self.tests, printf=printf, title="HCA Metrics")

  def exclude_test(self, exclude:Union[dict,list,str], testdict=None):
    """Exclude tests in exclude, keeping all others in self.tests"""
    if testdict is None:
      testdict = self.tests # entry point
    if isinstance(exclude, str):
      testdict.pop(exclude)
    elif isinstance(exclude, list):
      for k in exclude:
        self.exclude_test(k, testdict=testdict)
    else:
      for k, v in exclude.items():
        if len(v) == 0:
          # exclude whole category
          self.exclude_test(k, testdict=testdict)
        else:
          # recurse
          self.exclude_test(v, testdict=testdict[k])

  def add_test(self, include:Union[dict,list,str], out, testdict=None):
    """Only keep keys in the include list in self.tests"""
    
    if testdict is None:
      testdict = self.tests
    if isinstance(include, list):
      for k in include:
        self.add_test(k, out=out, testdict=testdict)
    elif isinstance(include, dict):
      for k, v in include.items():
        if k not in out:
          out[k] = {}
          self.add_test(v, out=out[k], testdict=testdict[k])
    elif isinstance(include, str):
      out[include] = testdict[include]
      

  def set_base(self, res:dict):
    self.base = HCAMetrics(self.lims, self.comp, self.tol, logger=self.logger)
    self.base.load_res(res, worst_case=True)

  def load_lims(self, lims:dict):
    """only copy limits for tests to be considered"""
    # self.lims = copy.deepcopy(lims)
    self.lims = {}
    for metric_class, metrics in lims.items():
      if metric_class in self.tests:
        self.lims[metric_class] = {}
        for metric, lim in metrics.items():
          if metric in self.tests[metric_class]:
            self.lims[metric_class][metric] = lim
            
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
  
  def get_vdiff_locations(self, lim=None):
    if lim is None:
      lim = self.lims["voltage"]["vdiff"]
    out = {"v": {}, "vdiff": {}}
    for reskey in ["pvdict", "recdict", "voltdict"]:
      for k, v in self.res[reskey].items():
        vbase = 1000*v["basekv"]/SQRT3
        if 100*v["vdiff"]/vbase > lim:
          out["v"][v["bus"]] = v["v"]/vbase
          out["vdiff"][v["bus"]] = 100*np.diff(v["v"])/vbase
    return out

  def get_violation_list(self):
    out = []
    for metric_class, metric in self.violation.items():
      out.extend([f"{metric_class}_{k}" for k in metric.keys()])
    return out

  def get_volt_buses(self, minmax, threshold=None):
    d = {}
    for reskey in ['pvdict', 'recdict', 'voltdict']:
      for k, v  in self.res[reskey].items():
          vbase = 1000*v["basekv"]/np.sqrt(3)
          if threshold is not None:
            tmp = threshold
          elif v["basekv"] < 1: #LV
            tmp = self.base.volt_stats.loc[f"{minmax}LVVoltage", "limits"]
          else: # MV
            tmp = self.base.volt_stats.loc[f"{minmax}Voltage", "limits"]
          if ((minmax == "Max") and (v["vmax"]/vbase > tmp)) or ((minmax == "Min") and (v["vmin"]/vbase < tmp)):
            d[v["bus"]] = v["v"]/vbase
    return d
  
  def get_volt_max_buses(self, threshold=None):
    return self.get_volt_buses("Max", threshold=threshold)

  def get_volt_min_buses(self, threshold=None):
    return self.get_volt_buses("Min", threshold=threshold)

  def get_thermal_branches(self, key=None):
    out = {}
    if key is None:
      for k in self.violation["thermal"].keys():
        out.update(**self.get_thermal_branches(key=k))
    else:
      for typ, name in self.violation["thermal"][key].index.str.split("."):
        if typ not in out:
          out[typ] = []
        out[typ].append(name)
    return out
  
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

  def _norm_hrs(self,val):
    if self.base is None:
      ## test 2: no branch is overloaded for more time than limit thermal->norm_hrs
      ov2 = self.res["di_overloads"].loc[:, "hrs_above_normal"]
      if ov2.empty:
        return True, 0
      else:
        return self._test(ov2, val, -1, self.tol["thermal"])
    else:
      mask = self.res["di_overloads"].index.isin(self.base.res["di_overloads"].index)
      ## test 1: any of the overloaded branches in base solution are not *more* overloaded
      ov1 = self.base.res["di_overloads"]["hrs_above_normal"].subtract(self.res["di_overloads"].loc[:, "hrs_above_normal"]).dropna()
      test1, margin1 = self._test(ov1, 0, 1, self.tol["thermal"])
      ## test 2: no new overloaded branch should be overloaded more than allowed hrs
      ov2 = self.res["di_overloads"].loc[~mask, "hrs_above_normal"]
      test2, margin2 = self._test(ov2, val, -1, self.tol["thermal"])
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
      pd.Series({i: np.abs(self.res["compflows"][i]["lims"].loc[["min", "max"], pq].apply(np.sign).sum()) - 1
                 for i in self.res["compflows"].keys()}, name=f"{pq}_dir")
                 for pq in ["p", "q"]], axis=1)
    return self._test(test, 0, 1, 0) # this is an integer test so tolerance is 0
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

    #test passes if for each component  at least 1 test is true [.any(axis=1)]
    # and this holds for all components [.any(axis=1).all()]
    return test.any(axis=1).all(), margin
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
    if violation_count > 0:
      self.last_violation_list = self.get_violation_list()
        
        


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
  print ("hca methods:")
  print ("Key                  Description")
  for key, description in hca_options.items():
    print(f"{key:20s} {description}")


def load_config(configin):
  ### get defaults
  # defaultsconfig = os.path.join(os.path.dirname(os.path.realpath(__file__)), "defaults.json")
  with resources.files("i2x.der_hca") as path:
    with open(os.path.join(path,"defaults.json")) as f:
      inputs = json.load(f)
  
  if isinstance(configin, dict):
    merge_configs(inputs, configin.copy())
  elif os.path.basename(configin) != 'defaults.json':
    with open(configin) as f:
      config = json.load(f)
    merge_configs(inputs, config)
  return inputs

def show_defaults():
  inputs = load_config('defaults.json')
  print_config(inputs)
