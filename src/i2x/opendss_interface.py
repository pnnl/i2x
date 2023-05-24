import py_dss_interface # .DSS as dss
import pkg_resources as pkg
import inspect
import numpy as np
from numpy import trapz
import os

def print_opendss_interface(doc_fp):
  dss = py_dss_interface.DSSDLL()
  print ('DSSDLL vars:', file=doc_fp)
  for row in vars(dss):
    print (' ', row, file=doc_fp)
  print ('DSSDLL dir:', file=doc_fp)
  for row in dir(dss):
    fn = getattr(dss, row)
    if inspect.ismethod(fn):
      print ('  {:40s} {:s}'.format (row, str(inspect.signature(fn))), file=doc_fp)

def dss_line (dss, line, debug_output):
  if debug_output:
    print ('dss: ', line)
  dss.text (line)

def initialize_opendss(choice, debug_output=True, **kwargs):
  """
  Load and compile the open dss feeder model
  """
  pwd = os.getcwd()
  dss = py_dss_interface.DSSDLL()
  fdr_path = pkg.resource_filename (__name__, 'models/{:s}'.format(choice))

  if debug_output:
    print ('default cache:', pkg.get_default_cache())
    print ('HCA feeder model path:', fdr_path)
    pkg.resource_listdir (__name__, 'models/{:s}'.format(choice))

  dss_line (dss, 'compile "{:s}/HCABase.dss"'.format (fdr_path), debug_output)
  os.chdir(pwd)
  return dss

def run_opendss(choice, pvcurve, loadmult, stepsize, numsteps, 
                loadcurve, invmode, invpf, solnmode, ctrlmode, 
                change_lines=None, debug_output=True, dss=None, **kwargs):

  # dss = py_dss_interface.DSSDLL()
  # fdr_path = pkg.resource_filename (__name__, 'models/{:s}'.format(choice))

  # if debug_output:
  #   print ('default cache:', pkg.get_default_cache())
  #   print ('HCA feeder model path:', fdr_path)
  #   pkg.resource_listdir (__name__, 'models/{:s}'.format(choice))

  # dss_line (dss, 'compile "{:s}/HCABase.dss"'.format (fdr_path), debug_output)

  if dss is None:
    dss = initialize_opendss(choice, debug_output=True, **kwargs)

  if change_lines is not None:
    for line in change_lines:
      dss_line (dss, line, debug_output)

  dss_line (dss, 'batchedit PVSystem..* irradiance=1 daily={:s} %cutin=0.1 %cutout=0.1 varfollowinverter=true'.format (pvcurve), debug_output) #kvarmax=?
  dss_line (dss, 'batchedit load..* daily={:s} duty={:s} yearly={:s}'.format (loadcurve, loadcurve, loadcurve), debug_output)
  if invmode == 'CONSTANT_PF':
    dss_line (dss, 'batchedit pvsystem..* pf={:.4f}'.format(invpf), debug_output)
  elif invmode == 'VOLT_WATT':
    dss_line (dss, 'batchedit pvsystem..* pf={:.4f}'.format(invpf), debug_output)
    dss_line (dss, 'new InvControl.vw mode=VOLTWATT voltage_curvex_ref=rated voltwatt_curve=voltwatt1547b deltaP_factor=0.02 EventLog=No', debug_output)
  elif invmode == 'VOLT_VAR_CATA':
    dss_line (dss, 'new InvControl.pv1 mode=VOLTVAR voltage_curvex_ref=rated vvc_curve1=voltvar1547a deltaQ_factor=0.4 RefReactivePower=VARMAX EventLog=No', debug_output)
  elif invmode == 'VOLT_VAR_CATB':
    dss_line (dss, 'new InvControl.pv1 mode=VOLTVAR voltage_curvex_ref=rated vvc_curve1=voltvar1547b deltaQ_factor=0.4 RefReactivePower=VARMAX EventLog=No', debug_output)
  elif invmode == 'VOLT_VAR_AVR':
    dss_line (dss, 'New ExpControl.pv1 deltaQ_factor=0.3 vreg=1.0 slope=22 vregtau=300 Tresponse=5 EventLog=No', debug_output)
  elif invmode == 'VOLT_VAR_VOLT_WATT':
    dss_line (dss, 'new InvControl.vv_vw combimode=VV_VW voltage_curvex_ref=rated vvc_curve1=voltvar1547b voltwatt_curve=voltwatt1547b deltaQ_factor=0.4 deltaP_factor=0.02 RefReactivePower=VARMAX EventLog=No', debug_output)
  elif invmode == 'VOLT_VAR_14H':
    dss_line (dss, 'new InvControl.vv_vw combimode=VV_VW voltage_curvex_ref=rated vvc_curve1=voltvar14h voltwatt_curve=voltwatt14h deltaQ_factor=0.4 deltaP_factor=0.02 RefReactivePower=VARMAX EventLog=No', debug_output)
  dss_line (dss, 'set loadmult={:.6f}'.format(loadmult), debug_output)
  dss_line (dss, 'set controlmode={:s}'.format(ctrlmode), debug_output)
  dss_line (dss, 'set maxcontroliter=1000', debug_output)
  dss_line (dss, 'set maxiter=30', debug_output)
  pvnames = dss.pvsystems_all_names()
  ## add pq and vi monitors to all pv systems
  for pvname in pvnames: # don't need to log all these
    dss.text ('new monitor.{:s}_pq element=pvsystem.{:s} terminal=1 mode=65 ppolar=no'.format (pvname, pvname))
    dss.text ('new monitor.{:s}_vi element=pvsystem.{:s} terminal=1 mode=96'.format (pvname, pvname))
#  dss.dssprogress_*() replaced by DSSProgress.exe calls over TCP/IP
  dss_line (dss, 'solve mode={:s} number={:d} stepsize={:d}s'.format(solnmode, numsteps, stepsize), debug_output)

  if debug_output:
    print ('{:d} PVSystems and {:d} generators'.format (dss.pvsystems_count(), dss.generators_count()))

  # initialize the outputs that are only filled in DUTY, DAILY, or other time series mode
  kWh_PV = 0.0
  kvarh_PV = 0.0
  pvdict = {}
  recdict = {}
  kWh_Net = 0.0
  kWh_Gen = 0.0
  kWh_Load = 0.0
  kWh_Loss = 0.0
  kWh_EEN = 0.0
  kWh_UE = 0.0
  kWh_OverN = 0.0
  kWh_OverE = 0.0

  # these outputs apply to SNAPSHOT and time series modes
  converged = bool(dss.solution_read_converged())
  if debug_output:
    print ('Converged = ', converged)
  num_cap_switches = 0
  num_tap_changes = 0
  num_relay_trips = 0
  for row in dss.solution_event_log():
    if ('Action=RESETTING' not in row) and ('Action=**RESET**' not in row) and ('Action=**ARMED**' not in row):
      if solnmode != 'DUTY' and debug_output:
        print (row)
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
    print ('{:4d} capacitor bank switching operations'.format (num_cap_switches))
    print ('{:4d} regulator tap changes'.format (num_tap_changes))
    print ('{:4d} relay trip operations'.format (num_relay_trips))
  if not converged:
    return {'converged': converged,
            'num_cap_switches': num_cap_switches,
            'num_tap_changes': num_tap_changes,
            'num_relay_trips': num_relay_trips}

  node_names = dss.circuit_all_node_names()
  node_vpus = dss.circuit_all_bus_vmag_pu()
#  print (bus_names)
#  print (bus_vpus)
  nnode = len(node_names)
  nvpu = len(node_vpus)
  if debug_output:
    print ('{:d} node names and {:d} vpu'.format (nnode, nvpu))
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
    print ('{:4d} node voltages below 0.95 pu,  lowest is {:.4f} pu at {:s} '.format (num_low_voltage, vminpu, node_vmin))
    print ('{:4d} node voltages above 1.05 pu, highest is {:.4f} pu at {:s}'.format (num_high_voltage, vmaxpu, node_vmax))

  if solnmode != 'SNAPSHOT':
    for name in pvnames:
      pvdict[name] = {'kWh':0.0, 'kvarh':0.0, 'vmin':0.0, 'vmax':0.0, 'vmean':0.0, 'vdiff':0.0}
    idx = dss.monitors_first()
    if idx > 0:
      hours = np.array(dss.monitors_dbl_hour())
      dh = hours[1] - hours[0]
    ## loop over monitor elements
    while idx > 0:
      name = dss.monitors_read_name() # name of monitor
      elem = dss.monitors_read_element() # name of monitored element
      if name.endswith('_rec_pq'):
        # recloser pq monitor
        # key = name[0:-7]
        key = elem.split(".")[1]
        p = np.array(dss.monitors_channel(1))
        q = np.array(dss.monitors_channel(2))
        if key not in recdict:
          # rec_pq OR rec_vi could occur first in the list
          recdict[key] = {}
          recdict[key]['elem'] = elem
          recdict[key]['monitor'] = name
        recdict[key]['pmin'] = np.min(p)
        recdict[key]['pmax'] = np.max(p)
        recdict[key]['p'] = p
        recdict[key]['qmin'] = np.min(q)
        recdict[key]['qmax'] = np.max(q)
        recdict[key]['q'] = q
      elif name.endswith('_rec_vi'):
        # recloser vi monitor
        # key = name[0:-7]
        key = elem.split(".")[1]
        v = np.array(dss.monitors_channel(1))
        amps = np.array(dss.monitors_channel(2))
        if key not in recdict:
          # rec_pq OR rec_vi could occur first in the list
          recdict[key] = {}
          recdict[key]['elem'] = elem
          recdict[key]['monitor'] = name
        recdict[key]['vmin'] = np.min(v)
        recdict[key]['vmax'] = np.max(v)
        recdict[key]['imin'] = np.min(amps)
        recdict[key]['imax'] = np.max(amps)
        recdict[key]['v'] = v
        recdict[key]['i'] = amps
      elif name.endswith('_pq'):
        # PV system pq monitor
        key = name[0:-3]
        p = np.array(dss.monitors_channel(1))
        q = np.array(dss.monitors_channel(2))
        ep = 0.0
        eq = 0.0
        if np.count_nonzero(np.isnan(p)) < 1:
          ep = -trapz (p, dx=dh)
        if np.count_nonzero(np.isnan(q)) < 1:
          eq = -trapz (q, dx=dh)
        kWh_PV += ep
        kvarh_PV += eq
        pvdict[key]['kWh'] = ep
        pvdict[key]['kvarh'] = eq
        pvdict[key]['p'] = p
        pvdict[key]['q'] = q
      elif name.endswith('_vi'):
        # PV system vi monitor
        key = name[0:-3]
        v = np.array(dss.monitors_channel(1))
        amps = np.array(dss.monitors_channel(2))
        vmin = np.min(v)
        vmax = np.max(v)
        vmean = np.mean(v)
        vdiff = np.max(np.abs(np.diff(v)))
        pvdict[key]['vmin'] = vmin
        pvdict[key]['vmax'] = vmax
        pvdict[key]['vmean'] = vmean
        pvdict[key]['vdiff'] = vdiff
        pvdict[key]['v'] = v
        pvdict[key]['i'] = i
      idx = dss.monitors_next()

    dss.meters_first()
    names = dss.meters_register_names()
    vals = dss.meters_register_values()
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
      print ('Srce  kWh = {:10.2f}'.format (kWh_Net))
      print ('Load  kWh = {:10.2f}'.format (kWh_Load))
      print ('Loss  kWh = {:10.2f}'.format (kWh_Loss))
      print ('Gen   kWh = {:10.2f}'.format (kWh_Gen))
      print ('PV    kWh = {:10.2f}'.format (kWh_PV))
      print ('PV  kvarh = {:10.2f}'.format (kvarh_PV))
      print ('EEN   kWh = {:10.2f}'.format (kWh_EEN))
      print ('UE    kWh = {:10.2f}'.format (kWh_UE))
  #  print ('OverN kWh = {:10.2f}'.format (kWh_OverN))
  #  print ('OverE kWh = {:10.2f}'.format (kWh_OverE))

  return {'converged': converged,
          'pvdict': pvdict,
          'recdict': recdict,
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

