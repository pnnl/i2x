import i2x.api as i2x
import random
import math

SQRT3 = math.sqrt(3.0)

def print_column_keys (label, d):
  columns = ''
  for key, row in d.items():
    columns = 'described by ' + str(row.keys())
    break
  print ('{:4d} {:20s} {:s}'.format (len(d), label, columns))

def pv_voltage_base_list (pvder, largeder):
  pvbases = {}
  for d in [pvder, largeder]:
    for key, row in d.items():  
      vnom = row['kv'] * 1000.0
      if row['phases'] > 1:
        vnom /= SQRT3
      pvbases[key] = vnom
  return pvbases

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
  for key, row in d['pvdict'].items():
    if key in pvbases:
      v_base = pvbases[key]
    else:
      v_base = 120.0
    row['vmin'] /= v_base
    row['vmax'] /= v_base
    row['vmean'] /= v_base
    row['vdiff'] /= v_base
    row['vdiff'] *= 100.0
    if row['vmin'] < pv_vmin:
      pv_vmin = row['vmin']
    if row['vmax'] > pv_vmax:
      pv_vmax = row['vmax']
    if row['vdiff'] > pv_vdiff:
      pv_vdiff = row['vdiff']
  print ('  Minimum PV Voltage        = {:.4f} pu'.format(pv_vmin))
  print ('  Maximum PV Voltage        = {:.4f} pu'.format(pv_vmax))
  print ('  Maximum PV Voltage Change = {:.4f} %'.format(pv_vdiff))

def print_large_der (largeder):
  print ('\nExisting DER:')
  for key, row in largeder.items():
    print (' ', key, row)

# This function adds appropriately sized PV to 100*pu_roofs % of the residential loads.
# The call to 'random' does not re-use any seed value, so repeated invocations will differ in results.
def append_rooftop_pv (change_lines, resloads, pu_roofs):
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
  print ('Added {:.2f} kW PV on {:d} residential rooftops'.format(rooftop_kw, rooftop_count))

def remove_large_der (change_lines, key, d):
  row = d[key]
  if row['type'] == 'solar':
    change_lines.append('edit pvsystem.{:s} enabled=no'.format(key))
  elif row['type'] == 'storage':
    change_lines.append('edit storage.{:s} enabled=no'.format(key))
  elif row['type'] == 'generator':
    change_lines.append('edit generator.{:s} enabled=no'.format(key))

def append_large_pv (change_lines, key, bus, kv, kva, kw, pvbases):
  change_lines.append('new pvsystem.{:s} bus1={:s} kv={:.3f} kva={:.3f} pmpp={:.3f} irrad=1'.format(key, bus, kv, kva, kw))
  pvbases[key] = 1000.0 * kv / SQRT3

def append_large_storage (change_lines, key, bus, kv, kva, kw, kwh):
  change_lines.append('new storage.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f} kwhrated={:.3f} kwhstored={:.3f}'.format(key, bus, kv, kva, kw, kwh, 0.5*kwh))

def append_large_generator (change_lines, key, bus, kv, kva, kw):
  change_lines.append('new generator.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f}'.format(key, bus, kv, kva, kw))

def redispatch_large_pv (change_lines, key, kva, kw):
  change_lines.append('edit pvsystem.{:s} kva={:.2f} pmpp={:.2f}'.format(key, kva, kw))

def redispatch_large_storage (change_lines, key, kva, kw):
  change_lines.append('edit storage.{:s} kva={:.2f} kw={:.2f}'.format(key, kva, kw))

def redispatch_large_generator (change_lines, key, kva, kw):
  change_lines.append('edit generator.{:s} kva={:.2f} kw={:.2f}'.format(key, kva, kw))

if __name__ == "__main__":
  print ('Feeder Model Choices for HCA')
  print ('Feeder       Path                 Base File')
  for key, row in i2x.feederChoices.items():
    print ('{:12s} {:20s} {:s}'.format (key, row['path'], row['base']))
  print ('\nSolar Profile Choices:', i2x.solarChoices.keys())
  print ('Load Profile Choices:', i2x.loadChoices.keys())
  print ('Inverter Choices:', i2x.inverterChoices.keys())
  print ('Solution Mode Choices:', i2x.solutionModeChoices)
  print ('Control Mode Choices:', i2x.controlModeChoices)

  feederName = 'ieee9500'
  G = i2x.load_builtin_graph(feederName)
  pvder, gender, batder, largeder, resloads, bus3phase, loadkw = i2x.parse_opendss_graph(G, bSummarize=False)

  print ('\nLoaded Feeder Model {:s}'.format(feederName))
  print_column_keys ('Large DER', largeder)
  print_column_keys ('Generators', gender)
  print_column_keys ('PV DER', pvder)
  print_column_keys ('Batteries', batder)
  print_column_keys ('Rooftop Candidates', resloads)
  # these are 3-phase buses without something else there, but the kV must be assumed
  print_column_keys ('Available 3-phase Buses', bus3phase) 

  print_large_der (largeder)

  pvbases = pv_voltage_base_list (pvder, largeder)
  change_lines = []
  if True:
    print ('\nMaking some experimental changes to the large DER')
    # delete some of the existing generators
    for key in ['pvfarm1', 'battery1', 'battery2', 'diesel590', 'diesel620', 'lngengine1800', 'lngengine100', 'microturb-2', 'microturb-3']:
      remove_large_der (change_lines, key, largeder)
    # add the PV and battery back in, with different names
    append_large_storage (change_lines, 'bat1new', 'm2001-ess1', 0.48, 250.0, 250.0, 1000.0)  # change from 2-hour to 4-hour
    append_large_storage (change_lines, 'bat2new', 'm2001-ess2', 0.48, 250.0, 250.0, 1000.0)  # change from 2-hour to 4-hour
    append_large_pv (change_lines, 'pvnew', 'm1047pv-3', 12.47, 1500.0, 1200.0, pvbases) # 200 kW larger than pvfarm1
    redispatch_large_generator (change_lines, 'steamgen1', 1000.0, 800.0) # reduce output by 800 kW
    for ln in change_lines:
      print (' ', ln)

  print ('\nAdding PV to 10% of the residential rooftops that don\'t already have PV')
  append_rooftop_pv (change_lines, resloads, 0.2)
  #change_lines.append('batchedit pvsystem..* enabled=no')

  d = i2x.run_opendss(choice = 'ieee9500',
                      pvcurve = 'pcloud', # 'pclear', 'pcloud', 'pvduty', 
                      invmode = 'CONSTANT_PF', # 'VOLT_VAR_VOLT_WATT', # 'VOLT_WATT', # 'VOLT_VAR_AVR', # 'VOLT_VAR', #'CONSTANT_PF',
                      invpf = 1.0,
                      loadmult = 1.0,
                      loadcurve = 'DEFAULT',
                      stepsize = 300, # 1,
                      numsteps = 288, # 2900,
                      solnmode = 'DAILY', # 'DUTY',
                      ctrlmode = 'STATIC',
                      change_lines = change_lines, 
                      debug_output = False)
  summary_outputs (d, pvbases)


