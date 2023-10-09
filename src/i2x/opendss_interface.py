import py_dss_interface
import pkg_resources as pkg
import inspect
import numpy as np
from numpy import trapz
import os

def print_class_doc (key, root, doc_fp):
  print ('-------------------------', file=doc_fp)
  print ('  {:s} {:s}'.format (key, root.__doc__), file=doc_fp)
  mbrs = dir(root)
  for row in mbrs:
    if row[0] != '_':
      print ('     ', row, file=doc_fp)

def print_opendss_interface(doc_fp):
  print ('Summmary of py-dss-interface methods', file=doc_fp)
  print ('See https://py-dss-interface.readthedocs.io/en/latest/index.html for more details\n', file=doc_fp)
  dss = py_dss_interface.DSS()
  mbrs = inspect.getmembers(dss)
  interfaces = {}
  print ('Properties', file=doc_fp)
  print ('==========================', file=doc_fp)
  for row in mbrs:
    name = row[0]
    val = row[1]
    if name[0] != '_' and not inspect.ismethod(val):
      classname = type(val).__name__
      if classname in ['str', 'bool']:
        print ('  ', name, classname, val, file=doc_fp)
      else:
        interfaces[name] = val
  print ('\nMethods', file=doc_fp)
  print ('==========================', file=doc_fp)
  for row in mbrs:
    name = row[0]
    val = row[1]
    if name[0] != '_' and inspect.ismethod(val):
      print ('  ', name, val.__doc__, inspect.signature(val), file=doc_fp)
  print ('\nInterfaces', file=doc_fp)
  print ('==========================', file=doc_fp)
  for key, val in interfaces.items():
    print_class_doc (key, val, doc_fp)

def dss_line (dss, line, debug_output, printf=print):
  if debug_output:
    printf ('dss: ' + line)
  dss.text (line)

def initialize_opendss(choice, debug_output=True, printf=print, **kwargs):
  """
  Load and compile the open dss feeder model
  """
  pwd = os.getcwd()
  dss = py_dss_interface.DSS()
  fdr_path = pkg.resource_filename (__name__, 'models/{:s}'.format(choice))

  if debug_output:
    printf ('default cache: ' + pkg.get_default_cache())
    printf ('HCA feeder model path: ' + fdr_path)
    printf ('OpenDSS path: ' + dss.dll_file_path)
    printf ('     version: ' + dss.dssinterface.version)
    pkg.resource_listdir (__name__, 'models/{:s}'.format(choice))

  dss_line (dss, 'compile "{:s}/HCABase.dss"'.format (fdr_path), debug_output, printf=printf)
  os.chdir(pwd)
  return dss

def get_event_log (dss):
  return dss.solution.event_log
  fname = dss.text ('export eventlog')
  print ('================')
  print ('log file at', fname)
  fp = open (fname, 'r')
  log = [line.rstrip() for line in fp]
  fp.close()
#  print (log)
  print ('================')
  return log

def run_opendss(choice, pvcurve, loadmult, stepsize, numsteps, 
                loadcurve, invmode, invpf, solnmode, ctrlmode, 
                change_lines=None, debug_output=True, dss=None, output=True,
                demandinterval=False, allow_forms=1, printf=print, **kwargs):

  # dss = py_dss_interface.DSS()
  # fdr_path = pkg.resource_filename (__name__, 'models/{:s}'.format(choice))

  # if debug_output:
  #   print ('default cache:', pkg.get_default_cache())
  #   print ('HCA feeder model path:', fdr_path)
  #   pkg.resource_listdir (__name__, 'models/{:s}'.format(choice))

  # dss_line (dss, 'compile "{:s}/HCABase.dss"'.format (fdr_path), debug_output)

  if dss is None:
    dss = initialize_opendss(choice, debug_output=debug_output, printf=printf, **kwargs)

  if change_lines is not None:
    for line in change_lines:
      dss_line (dss, line, debug_output, printf=printf)

  dss_line (dss, 'batchedit PVSystem..* irradiance=1 daily={:s} %cutin=0.1 %cutout=0.1 varfollowinverter=true'.format (pvcurve), debug_output, printf=printf) #kvarmax=?
  dss_line (dss, 'batchedit load..* daily={:s} duty={:s} yearly={:s}'.format (loadcurve, loadcurve, loadcurve), debug_output, printf=printf)
  if dss.pvsystems.count > 0:
    if invmode == 'CONSTANT_PF':
      dss_line (dss, 'batchedit pvsystem..* pf={:.4f}'.format(invpf), debug_output, printf=printf)
    elif invmode == 'VOLT_WATT':
      dss_line (dss, 'batchedit pvsystem..* pf={:.4f}'.format(invpf), debug_output, printf=printf)
      dss_line (dss, 'new InvControl.vw mode=VOLTWATT voltage_curvex_ref=rated voltwatt_curve=voltwatt1547b deltaP_factor=0.02 EventLog=No', debug_output, printf=printf)
    elif invmode == 'VOLT_VAR_CATA':
      dss_line (dss, 'new InvControl.pv1 mode=VOLTVAR voltage_curvex_ref=rated vvc_curve1=voltvar1547a deltaQ_factor=0.4 RefReactivePower=VARMAX EventLog=No', debug_output, printf=printf)
    elif invmode == 'VOLT_VAR_CATB':
      dss_line (dss, 'new InvControl.pv1 mode=VOLTVAR voltage_curvex_ref=rated vvc_curve1=voltvar1547b deltaQ_factor=0.4 RefReactivePower=VARMAX EventLog=No', debug_output, printf=printf)
    elif invmode == 'VOLT_VAR_AVR':
      dss_line (dss, 'New ExpControl.pv1 deltaQ_factor=0.3 vreg=1.0 slope=22 vregtau=300 Tresponse=5 EventLog=No', debug_output, printf=printf)
    elif invmode == 'VOLT_VAR_VOLT_WATT':
      dss_line (dss, 'new InvControl.vv_vw combimode=VV_VW voltage_curvex_ref=rated vvc_curve1=voltvar1547b voltwatt_curve=voltwatt1547b deltaQ_factor=0.4 deltaP_factor=0.02 RefReactivePower=VARMAX EventLog=No', debug_output, printf=printf)
    elif invmode == 'VOLT_VAR_14H':
      dss_line (dss, 'new InvControl.vv_vw combimode=VV_VW voltage_curvex_ref=rated vvc_curve1=voltvar14h voltwatt_curve=voltwatt14h deltaQ_factor=0.4 deltaP_factor=0.02 RefReactivePower=VARMAX EventLog=No', debug_output, printf=printf)
  dss_line (dss, 'set loadmult={:.6f}'.format(loadmult), debug_output, printf=printf)
  dss_line (dss, 'set controlmode={:s}'.format(ctrlmode), debug_output, printf=printf)
  dss_line (dss, 'set maxcontroliter=1000', debug_output, printf=printf)
  dss_line (dss, 'set maxiter=30', debug_output, printf=printf)
  
  ### collect all existing monitors by monitored element and mode
  existing_monitors = []
  idx = dss.monitors.first()
  while idx > 0:
    existing_monitors.append((dss.monitors.element, dss.monitors.mode))
    idx = dss.monitors.next()
  ### check if reclosers are monitored
  idx = dss.reclosers.first()
  while idx > 0:
    elem = dss.reclosers.monitored_obj
    if (elem, 65) not in existing_monitors:
      ## add pq monitor
      dss_line (dss, f'new monitor.{elem.split(".")[1]}_rec_pq element={elem} terminal={dss.reclosers.monitored_term} mode=65 ppolar=no', debug_output, printf=printf)
      ## add vi monitor (this may be duplicate due to all the voltage monitors)
      dss_line (dss, f'new monitor.{elem.split(".")[1]}_rec_vi element={elem} terminal={dss.reclosers.monitored_term} mode=96', debug_output, printf=printf)
    idx = dss.reclosers.next()

  pvnames = dss.pvsystems.names
  if dss.pvsystems.count > 0:
    ## add pq and vi monitors to all pv systems
    for pvname in pvnames: # don't need to log all these
      if f"{pvname}_pq" not in dss.monitors.names:
        dss.text ('new monitor.{:s}_pq element=pvsystem.{:s} terminal=1 mode=65 ppolar=no'.format (pvname, pvname))
      if f"{pvname}_vi" not in dss.monitors.names:
        dss.text ('new monitor.{:s}_vi element=pvsystem.{:s} terminal=1 mode=96'.format (pvname, pvname))
  
  if dss.generators.count > 0:
    ## add pq monitors to all generators
    for genname in dss.generators.names:
      if f"{genname}_gen_pq" not in dss.monitors.names:
        dss_line (dss, 'new monitor.{:s}_gen_pq element=generator.{:s} terminal=1 mode=65 ppolar=no'.format (genname, genname), debug_output, printf=printf)

  if demandinterval:
    ## add voltage and thermal reporting
    dss_line(dss, 'set overloadreport=true', debug_output, printf=printf) #activate the overload (thermal) report
    dss_line(dss, 'set voltexceptionreport=true', debug_output, printf=printf) #voltage violation
    dss_line(dss, 'set DemandInterval=TRUE', debug_output, printf=printf)
    dss_line(dss, 'set DIVerbose=TRUE', debug_output, printf=printf)
  
    dss_line(dss, f'set DataPath="{os.getcwd()}"', debug_output, printf=printf)

  dss.dssinterface.allow_forms = allow_forms
  dss_line (dss, 'solve mode={:s} number={:d} stepsize={:d}s'.format(solnmode, numsteps, stepsize), debug_output, printf=printf)
  if demandinterval:
    dss_line(dss, 'closedi', debug_output, printf=printf)
  if output:
    return opendss_output(dss, solnmode, pvnames, debug_output=debug_output, printf=printf, **kwargs)
  
def opendss_output(dss, solnmode, pvnames, debug_output=True, printf=print, **kwargs):
  if debug_output:
    printf ('{:d} PVSystems and {:d} generators'.format (dss.pvsystems.count, dss.generators.count))

  # initialize the outputs that are only filled in DUTY, DAILY, or other time series mode
  kWh_PV = 0.0
  kvarh_PV = 0.0
  pvdict = {}
  gendict = {}
  recdict = {}
  voltdict = {}
  kWh_Net = 0.0
  kWh_Gen = 0.0
  kWh_Load = 0.0
  kWh_Loss = 0.0
  kWh_EEN = 0.0
  kWh_UE = 0.0
  kWh_OverN = 0.0
  kWh_OverE = 0.0

  # these outputs apply to SNAPSHOT and time series modes
  converged = bool(dss.solution.converged)
  if debug_output:
    printf (f'Converged = {converged}')
  num_cap_switches = 0
  num_tap_changes = 0
  num_relay_trips = 0
  for row in get_event_log (dss):
    if ('Action=RESETTING' not in row) and ('Action=**RESET**' not in row) and ('Action=**ARMED**' not in row):
      if solnmode != 'DUTY' and debug_output:
        printf (row)
    if 'Element=Relay' in row:
      if 'Action=OPENED' in row:
        num_relay_trips += 1
    if 'Element=Capacitor' in row:
      if '**OPENED**' in row or '**CLOSED**' in row:
        num_cap_switches += 1
    if 'Element=Regulator' in row:
      if 'CHANGED' in row and 'TAP' in row:
        num_tap_changes += abs(int(row.split()[6]))
  if debug_output:
    printf ('{:4d} capacitor bank switching operations'.format (num_cap_switches))
    printf ('{:4d} regulator tap changes'.format (num_tap_changes))
    printf ('{:4d} relay trip operations'.format (num_relay_trips))
  if not converged:
    return {'converged': converged,
            'num_cap_switches': num_cap_switches,
            'num_tap_changes': num_tap_changes,
            'num_relay_trips': num_relay_trips}

  node_names = dss.circuit.nodes_names
  node_vpus = dss.circuit.buses_vmag_pu
#  print (bus_names)
#  print (bus_vpus)
  nnode = len(node_names)
  nvpu = len(node_vpus)
  if debug_output:
    printf ('{:d} node names and {:d} vpu'.format (nnode, nvpu))
  vminpu = 100.0
  vmaxpu = 0.0
  node_vmin = ''
  node_vmax = ''
  num_low_voltage = 0
  num_high_voltage = 0
  for i in range(nnode):
    v = node_vpus[i]
    if v < vminpu:
      vminpu = v
      node_vmin = node_names[i]
    if v > vmaxpu:
      vmaxpu = v
      node_vmax = node_names[i]
    if v < 0.95:
      num_low_voltage += 1
    if v > 1.05:
      num_high_voltage += 1
  if debug_output:
    printf ('{:4d} final node voltages below 0.95 pu,  lowest is {:.4f} pu at {:s} '.format (num_low_voltage, vminpu, node_vmin))
    printf ('{:4d} final node voltages above 1.05 pu, highest is {:.4f} pu at {:s}'.format (num_high_voltage, vmaxpu, node_vmax))

  if solnmode != 'SNAPSHOT':
    # for name in pvnames:
    #   pvdict[name] = {'kWh':0.0, 'kvarh':0.0, 'vmin':0.0, 'vmax':0.0, 'vmean':0.0, 'vdiff':0.0}
    idx = dss.monitors.first()
    if idx > 0:
      hours = np.array(dss.monitors.dbl_hour)
      dh = hours[1] - hours[0]
    ## loop over monitor elements
    while idx > 0:
      name = dss.monitors.name # name of monitor
      elem = dss.monitors.element # name of monitored element
      if check_element_status(dss, elem) == 0:
        # element is not active, skip
        idx = dss.monitors.next()
        continue
      if name.endswith('_rec_pq'):
        # recloser pq monitor
        # key = name[0:-7]
        key = elem.split(".")[1]
        get_pq_monitor(dss, key, elem, name, recdict, dh=dh)
      elif name.endswith('_rec_vi'):
        # recloser vi monitor
        # key = name[0:-7]
        key = elem.split(".")[1]
        get_vi_monitor(dss, key, elem, name, recdict)
      elif name.endswith("_volt_vi"):
        # voltage monitor 
        key = name[:-8] #this is the bus name
        get_vi_monitor(dss, key, elem, name, voltdict)
      elif name.endswith('_gen_pq'):
        # generator pq monitor
        # key = name[0:-7]
        key = elem.split(".")[1]
        get_pq_monitor(dss, key, elem, name, gendict, dh=dh)
      elif name.endswith('_pq'):
        # PV system pq monitor
        key = name[0:-3]
        get_pq_monitor(dss, key, elem, name, pvdict, dh=dh)
        kWh_PV += pvdict[key]["kWh"]
        kvarh_PV += pvdict[key]["kvarh"]
      elif name.endswith('_vi'):
        # PV system vi monitor
        key = name[0:-3]
        get_vi_monitor(dss, key, elem, name, pvdict)
      idx = dss.monitors.next()

    dss.meters.first()
    names = dss.meters.register_names
    vals = dss.meters.register_values
    for i in range (len(vals)):
  #    print ('{:30s} {:13.6f}'.format (names[i], vals[i]))
      if names[i] == 'kWh':
        kWh_Net = vals[i]
      if num_relay_trips < 1:
        if names[i] == 'Gen kWh':
          kWh_Gen = vals[i]
        if names[i] == 'Zone kWh':
          kWh_Load = vals[i]
        if names[i] == 'Zone Losses kWh':
          kWh_Loss = vals[i]
        if names[i] == 'Load EEN':
          kWh_EEN = vals[i]
        if names[i] == 'Load UE':
          kWh_UE = vals[i]
        if names[i] == 'Overload kWh Normal':
          kWh_OverN = vals[i]
        if names[i] == 'Overload kWh Emerg':
          kWh_OverE = vals[i]
    if debug_output:
      printf ('Srce  kWh = {:10.2f}'.format (kWh_Net))
      printf ('Load  kWh = {:10.2f}'.format (kWh_Load))
      printf ('Loss  kWh = {:10.2f}'.format (kWh_Loss))
      printf ('Gen   kWh = {:10.2f}'.format (kWh_Gen))
      printf ('PV    kWh = {:10.2f}'.format (kWh_PV))
      printf ('PV  kvarh = {:10.2f}'.format (kvarh_PV))
      printf ('EEN   kWh = {:10.2f}'.format (kWh_EEN))
      printf ('UE    kWh = {:10.2f}'.format (kWh_UE))
  #  print ('OverN kWh = {:10.2f}'.format (kWh_OverN))
  #  print ('OverE kWh = {:10.2f}'.format (kWh_OverE))

  return {'converged': converged,
          'pvdict': pvdict,
          'gendict': gendict,
          'recdict': recdict,
          'voltdict': voltdict,
          'num_cap_switches': num_cap_switches,
          'num_tap_changes': num_tap_changes,
          'num_relay_trips': num_relay_trips,
          'num_low_voltage': num_low_voltage,
          'num_high_voltage': num_high_voltage,
          'vminpu': vminpu, 
          'node_vmin': node_vmin,
          'vmaxpu': vmaxpu, 
          'node_vmax': node_vmax,
          'kWh_Net':kWh_Net,
          'kWh_Load':kWh_Load,
          'kWh_Loss':kWh_Loss,
          'kWh_Gen':kWh_Gen,
          'kWh_PV':kWh_PV,
          'kvarh_PV':kvarh_PV,
          'kWh_EEN':kWh_EEN,
          'kWh_UE':kWh_UE,
          'kWh_OverN':kWh_OverN,
          'kWh_OverE':kWh_OverE,
          'dss': dss}

def get_vi_monitor(dss:py_dss_interface.DSSDLL, key:str, elem:str, name:str, d:dict):
  """update dictionary d at `key` with values from a voltage/current monitor
  `elem`: name of monitored element
  `name`: name of monitor object
  `d`: dictionary to be updated
  """
  v = np.array(dss.monitors.channel(1))
  amps = np.array(dss.monitors.channel(2))
  if key not in d:
    d[key] = {}
    d[key]['elem'] = elem
    d[key]['monitor'] = name
    d[key]['basekv'] = get_basekv(dss, elem, dss.monitors.terminal)
    d[key]['bus'] = get_bus(dss, elem, dss.monitors.terminal)
    # d[key]['basekv'] = np.unique(get_basekv(dss, elem)).squeeze() # should lead to a single float except for transformers
  d[key]['vmin'] = np.min(v)
  d[key]['vmax'] = np.max(v)
  d[key]['vmean'] = np.mean(v)
  d[key]['vdiff'] = np.max(np.abs(np.diff(v)))
  d[key]['imin'] = np.min(amps)
  d[key]['imax'] = np.max(amps)
  d[key]['v'] = v
  d[key]['i'] = amps

def get_pq_monitor(dss:py_dss_interface.DSSDLL, key:str, elem:str, name:str, d:dict, dh=0):
  p = np.array(dss.monitors.channel(1))
  q = np.array(dss.monitors.channel(2))
  if key not in d:
    d[key] = {}
    d[key]['elem'] = elem
    d[key]['monitor'] = name
    d[key]['basekv'] = get_basekv(dss, elem, dss.monitors.terminal)
    d[key]['bus'] = get_bus(dss, elem, dss.monitors.terminal)
    # d[key]['basekv'] = np.unique(get_basekv(dss, elem)).squeeze() # should lead to a single float except for transformers
  d[key]['pmin'] = np.min(p)
  d[key]['pmax'] = np.max(p)
  d[key]['p'] = p
  d[key]['qmin'] = np.min(q)
  d[key]['qmax'] = np.max(q)
  d[key]['q'] = q
  if dh > 0:
    # calculate energy
    ep = 0.0
    eq = 0.0
    if np.count_nonzero(np.isnan(p)) < 1:
      ep = -trapz (p, dx=dh)
    if np.count_nonzero(np.isnan(q)) < 1:
      eq = -trapz (q, dx=dh)
    d[key]['kWh'] = ep
    d[key]['kvarh'] = eq

def check_element_status(dss:py_dss_interface.DSSDLL, elemname:str) -> int:
  index_str = dss.circuit.set_active_element(elemname)
  return dss.cktelement.is_enabled

def get_basekv(dss:py_dss_interface.DSSDLL, elemname:str, terminal:int) -> float:
  dss.circuit.set_active_element(elemname)
  
  # set the bus of the specified terminal active
  dss.circuit.set_active_bus(dss.cktelement.bus_names[terminal-1])
  return dss.bus.kv_base*np.sqrt(3)

def get_bus(dss:py_dss_interface.DSSDLL, elemname:str, terminal:int) -> str:
  dss.circuit.set_active_element(elemname)
  
  # set the bus of the specified terminal active
  dss.circuit.set_active_bus(dss.cktelement.bus_names[terminal-1])
  return dss.bus.name