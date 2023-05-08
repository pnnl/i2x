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

SQRT3 = math.sqrt(3.0)

def print_column_keys (label, d):
  columns = ''
  for key, row in d.items():
    columns = 'described by ' + str(row.keys())
    break
  print ('{:4d} {:20s} {:s}'.format (len(d), label, columns))

def pv_voltage_base_list (pvder, largeder, **kwargs):
  pvbases = {}
  for d in [pvder, largeder]:
    for key, row in d.items():  
      vnom = row['kv'] * 1000.0
      if row['phases'] > 1:
        vnom /= SQRT3
      pvbases[key] = vnom
  return pvbases

def check_element_status(dss:py_dss_interface.DSSDLL, elemname:str) -> int:
  index_str = dss.circuit_set_active_element(elemname)
  return dss.cktelement_read_enabled()

def summary_outputs (d, pvbases):
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
      print ('  {:10s} {:8.2f} {:8.2f}  {:8.2f} {:8.2f}  {:8.2f} {:8.2f}  {:7.2f} {:7.2f}'.format (key, 
                                                                                              row['pmin'], row['pmax'],
                                                                                              row['qmin'], row['qmax'],
                                                                                              row['vmin'], row['vmax'],
                                                                                              row['imin'], row['imax']))

def print_large_der (largeder):
  print ('\nExisting DER:')
  for key, row in largeder.items():
    print (' ', key, row)

# This function adds appropriately sized PV to 100*pu_roofs % of the residential loads.
# The call to 'random' does not re-use any seed value, so repeated invocations will differ in results.
def append_rooftop_pv (change_lines, G, resloads, pu_roofs, seed=None):
  """
  This function adds appropriately sized PV to 100*pu_roofs % of the residential loads.
  The optional seed argument for the random number generator can take either: 
    - None (default): Operating system defaults will be used
    - 'hash': the hash of graph G, will be used as the seed.
                        As a result, calls on exactly the same graph will be reproducible.
    - Int: any integer value will be passed directly to the seed function.
  """

  if seed == 'hash':
    random.seed(hash(G))
  else:
    random.seed(seed)

  rooftop_kw = 0.0
  rooftop_count = 0
  if (pu_roofs < 0.0) or (pu_roofs > 1.0):
    print ('Portion of PV Rooftops {:.4f} must lie between 0 and 1, inclusive'.format(pu_roofs))
  else:
    for key, row in resloads.items():
      if random.random() <= pu_roofs:
        bus = row['bus']
        kv = row['kv']
        kw = row['derkw']
        kva = kw * 1.21 # TODO: Cat A or Cat B
        rooftop_kw += kw
        rooftop_count += 1
        change_lines.append('new pvsystem.{:s} bus1={:s}.1.2 phases=2 kv={:.3f} kva={:.2f} pmpp={:.2f} irrad=1.0 pf=1.0'.format (key, bus, kv, kva, kw))
        G.nodes[bus]["nclass"] = 'solar' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
        G.nodes[bus]["ndata"]["pvkva"] = kva
        G.nodes[bus]["ndata"]["pvkw"] = kw
        G.nodes[bus]["ndata"]["kv"] = kv
        G.nodes[bus]["ndata"]["shunts"].append(f"pvsystem.{key}")
  print ('Added {:.2f} kW PV on {:d} residential rooftops'.format(rooftop_kw, rooftop_count))

def remove_large_der (change_lines, G, key, d):
  try:
    row = d[key]
  except KeyError:
    ## if der was already removed by some other method
    ## we could end up here
    return 
  if row['type'] == 'solar':
    change_lines.append('edit pvsystem.{:s} enabled=no'.format(key))
    G.nodes[row["bus"]]["ndata"]["pvkva"] = 0
    G.nodes[row["bus"]]["ndata"]["pvkw"] = 0
  elif row['type'] == 'storage':
    change_lines.append('edit storage.{:s} enabled=no'.format(key))
    G.nodes[row["bus"]]["ndata"]["batkva"] = 0
    G.nodes[row["bus"]]["ndata"]["batkw"] = 0
  elif row['type'] == 'generator':
    change_lines.append('edit generator.{:s} enabled=no'.format(key))
    G.nodes[row["bus"]]["ndata"]["genkva"] = 0
    G.nodes[row["bus"]]["ndata"]["genkw"] = 0
  else:
    return
  
  ## update graph (no need to return, G should be passed by reference)
  # remove the element from the shunt list
  sidx = np.where( [key in s for s in G.nodes[row["bus"]]["ndata"]["shunts"]])[0][0]
  G.nodes[row["bus"]]["ndata"]["shunts"].pop(sidx)
  G.nodes[row["bus"]]["nclass"] = update_node_class(G, row["bus"])

def remove_all_pv(change_lines, G):
  change_lines.append('batchedit pvsystem..* enabled=no')
  for n, d in G.nodes(data=True):
    if d.get("nclass") == 'solar':
      d["ndata"]["pvkva"] = 0.0
      d["ndata"]["pvkw"] = 0.0
      shunts_new = [s for s in d["ndata"]["shunts"] if 'pvsystem' not in s]
      d["ndata"]["shunts"] = shunts_new
      d["nclass"] = update_node_class(G, n)

def append_large_pv (change_lines, G, pvbases, key, bus, kv, kva, kw):
  change_lines.append('new pvsystem.{:s} bus1={:s} kv={:.3f} kva={:.3f} pmpp={:.3f} irrad=1'.format(key, bus, kv, kva, kw))
  pvbases[key] = 1000.0 * kv / SQRT3
  G.nodes[bus]["nclass"] = 'solar' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
  G.nodes[bus]["ndata"]["pvkva"] = kva
  G.nodes[bus]["ndata"]["pvkw"] = kw
  G.nodes[bus]["ndata"]["nomkv"] = kv
  G.nodes[bus]["ndata"]["shunts"].append(f"pvsystem.{key}")

def append_large_storage (change_lines, G, key, bus, kv, kva, kw, kwh):
  change_lines.append('new storage.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f} kwhrated={:.3f} kwhstored={:.3f}'.format(key, bus, kv, kva, kw, kwh, 0.5*kwh))
  G.nodes[bus]["nclass"] = 'storage' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
  G.nodes[bus]["ndata"]["batkva"] = kva
  G.nodes[bus]["ndata"]["batkw"] = kw
  G.nodes[bus]["ndata"]["batkwh"] = kwh
  G.nodes[bus]["ndata"]["nomkv"] = kv
  G.nodes[bus]["ndata"]["shunts"].append(f"storage.{key}")

def append_large_generator (change_lines, G, key, bus, kv, kva, kw):
  change_lines.append('new generator.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f}'.format(key, bus, kv, kva, kw))
  G.nodes[bus]["nclass"] = 'generator' # TODO: can we put multiple elements at one bus, if so, won't this overwrite?
  G.nodes[bus]["ndata"]["genkva"] = kva
  G.nodes[bus]["ndata"]["genkw"] = kw
  G.nodes[bus]["ndata"]["nomkv"] = kv
  G.nodes[bus]["ndata"]["shunts"].append(f"generator.{key}")

def redispatch_large_pv (change_lines, G, key, kva, kw):
  change_lines.append('edit pvsystem.{:s} kva={:.2f} pmpp={:.2f}'.format(key, kva, kw))
  bus = get_node_from_classkey(G, "pvsystem", key)
  G.nodes[bus]["ndata"]["pvkva"] = kva
  G.nodes[bus]["ndata"]["pvkw"] = kw

def redispatch_large_storage (change_lines, G, key, kva, kw):
  change_lines.append('edit storage.{:s} kva={:.2f} kw={:.2f}'.format(key, kva, kw))
  bus = get_node_from_classkey(G, "storage", key)
  G.nodes[bus]["ndata"]["batkva"] = kva
  G.nodes[bus]["ndata"]["batkw"] = kw

def redispatch_large_generator (change_lines, G, key, kva, kw):
  change_lines.append('edit generator.{:s} kva={:.2f} kw={:.2f}'.format(key, kva, kw))
  bus = get_node_from_classkey(G, "generator", key)
  G.nodes[bus]["ndata"]["genkva"] = kva
  G.nodes[bus]["ndata"]["genkw"] = kw

def get_node_from_classkey(G, nclass, key):
  """Retrive the bus name where shunt nclass.key is connected
  From graph G
  """
  
  for n, d in G.nodes(data=True):
    try:
      if np.any([f"{nclass}.{key}" == s for s in d["ndata"]["shunts"]]):
        return n
    except KeyError:
      pass

def update_node_class(G, n):
  nclass  = "bus"
  try:
    if G.nodes[n]["ndata"]["shunts"]:
      nclass = G.nodes[n]["ndata"]["shunts"][-1].split(".")[0]
      if nclass == 'pvsystem':
        nclass = 'solar'
  except KeyError:
    pass
  return nclass

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


def print_parsed_graph(pvder, gender, batder, largeder, resloads, bus3phase, all3phase, **kwargs):
  print_column_keys ('Large DER (>=100 kVA)', largeder)
  print_column_keys ('Generators', gender)
  print_column_keys ('PV DER', pvder)
  print_column_keys ('Batteries', batder)
  print_column_keys ('Rooftop Candidates (2ph & < 1kV)', resloads)
  # these are 3-phase buses without something else there, but the kV must be assumed
  print_column_keys ('Available 3-phase Buses', bus3phase)
  print_column_keys ('All 3-phase Buses', all3phase) 
  print_large_der (largeder)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="i2X Hosting Capacity Analysis")
  parser.add_argument("config", nargs='?', help="configuration file", default="defaults.json")
  parser.add_argument("--show-options", help="Show options and exit", action='store_true')
  parser.add_argument("--print-inputs", help="print passed inputs", action="store_true")
  args = parser.parse_args()

  if args.show_options:
    print_options()
    sys.exit(0)
  
  ### get defaults
  with open('defaults.json') as f:
    inputs = json.load(f)
  
  if args.config != 'defaults.json':
    with open(args.config) as f:
      config = json.load(f)
    for k,v in config.items():
      if k not in inputs:
        print(f"WARNING: configuration parameter {k} is unknown. Check spelling and capitalization perhaps?")
      inputs[k] = v
  
  if args.print_inputs:
    print("Provided/Default Inputs:\n===============")
    for k,v in inputs.items():
      print(f"{k}: {v}")
  
  G = i2x.load_builtin_graph(inputs["feederName"])
  graph_dirs = i2x.parse_opendss_graph(G, bSummarize=False)

  print ('\nLoaded Feeder Model {:s}'.format(inputs["feederName"]))
  print_parsed_graph(**graph_dirs)


  pvbases = pv_voltage_base_list (**graph_dirs)

  print(f'\nnode m1047pv-3: {G.nodes["m1047pv-3"]}')
  print(f"pvfarm1: {pvbases.get('pvfarm1')}")
  change_lines = []
  # if True:
  #   print ('\nMaking some experimental changes to the large DER')
  #   # delete some of the existing generators
  #   for key in ['pvfarm1', 'battery1', 'battery2', 'diesel590', 'diesel620', 'lngengine1800', 'lngengine100', 'microturb-2', 'microturb-3']:
  #     remove_large_der (change_lines, key, largeder, G)
  #   # add the PV and battery back in, with different names
  #   append_large_storage (change_lines, 'bat1new', 'm2001-ess1', 0.48, 250.0, 250.0, 1000.0)  # change from 2-hour to 4-hour
  #   append_large_storage (change_lines, 'bat2new', 'm2001-ess2', 0.48, 250.0, 250.0, 1000.0)  # change from 2-hour to 4-hour
  #   append_large_pv (change_lines, 'pvnew', 'm1047pv-3', 12.47, 1500.0, 1200.0, pvbases) # 200 kW larger than pvfarm1
  #   redispatch_large_generator (change_lines, 'steamgen1', 1000.0, 800.0) # reduce output by 800 kW
  #   for ln in change_lines:
  #     print (' ', ln)
  print ('\nMaking some deterministic changes')
  ### remove all pv 
  if inputs["remove_all_pv"]:
    remove_all_pv(change_lines, G)
    graph_dirs = i2x.parse_opendss_graph(G, bSummarize=False)
  print(f'\nnode m1047pv-3: {G.nodes["m1047pv-3"]}')
  print(f"pvfarm1: {pvbases.get('pvfarm1')}")
  ### remove specified large ders
  for key in inputs["remove_large_der"]:
    remove_large_der(change_lines, G, key, graph_dirs["largeder"])
  graph_dirs = i2x.parse_opendss_graph(G, bSummarize=False)
  print(f'\nnode m1047pv-3: {G.nodes["m1047pv-3"]}')
  print(f"pvfarm1: {pvbases.get('pvfarm1')}")
  
  ### add new specified storage
  for key, val in inputs["explicit_storage"].items():
    append_large_storage(change_lines, G, key, **val)
  graph_dirs = i2x.parse_opendss_graph(G, bSummarize=False)

  print(f'\nnode m1047pv-3: {G.nodes["m1047pv-3"]}')
  print(f"pvfarm1: {pvbases.get('pvfarm1')}")

  ### add new pv
  for key, val in inputs["explicit_pv"].items():
    append_large_pv(change_lines, G, pvbases, key, **val)
    graph_dirs = i2x.parse_opendss_graph(G, bSummarize=False)
    pvbases = pv_voltage_base_list (**graph_dirs)
  
  print(f'\nnode m1047pv-3: {G.nodes["m1047pv-3"]}')
  print(f"pvfarm1: {pvbases.get('pvfarm1')}")

  ### redispatch existing generators
  for key, val in inputs["redisp_gen"].items():
    redispatch_large_generator(change_lines, G, key, **val)
  
  for ln in change_lines:
    print (' ', ln)
  
  ### post explicit change parsing:
  graph_dirs = i2x.parse_opendss_graph(G, bSummarize=False)
  print(f"\nFeeder description following deterministic changes:")
  print_parsed_graph(**graph_dirs)

  ### base rooftop pv
  print (f'\nAdding PV to {inputs["res_pv_frac"]*100}% of the residential rooftops that don\'t already have PV')
  append_rooftop_pv (change_lines, G, graph_dirs["resloads"], inputs["res_pv_frac"])
  
  graph_dirs = i2x.parse_opendss_graph(G, bSummarize=False)
  pvbases = pv_voltage_base_list (**graph_dirs)
  print("\nFeeder description following intialization changes:")
  print_parsed_graph(**graph_dirs)

  print(f"unique pvbases:\n{np.unique([np.round(x,3) for x in pvbases.values()])}")
  print(f'\nnode m1047pv-3: {G.nodes["m1047pv-3"]}')
  print(f"pvfarm1: {pvbases.get('pvfarm1')}")

  comps, reclosers = isl.get_islands(G)
  print('\nIslanding Considerations:\n')
  print(f'{len(comps)} components found based on recloser positions')
  for i, c in enumerate(comps):
    isl.show_component(G, comps, i, printvals=True, printheader=i==0, plot=False)

  inputs["choice"] = inputs["feederName"]
  inputs["change_lines"] = change_lines
  d = i2x.run_opendss(**inputs)
  summary_outputs (d, pvbases)


