# usage 'python3 plots.py metrics_root'
import sys
import os
import tesp_support.process_gld as gp
import tesp_support.process_inv as ip
import tesp_support.process_voltages as vp
import matplotlib as mpl;
import matplotlib.pyplot as plt;
import numpy as np;

meters = ['hub_mtr', 'homes_mtr_A', 'homes_mtr_B', 'homes_mtr_C', 'fdr_head', 'hub_bess_mtr', 'hub_dg_mtr', 'hub_pv_mtr']
tticks = [0, 24, 48, 72, 96, 120, 144, 168]

def summarize_metrics (dict):
#  print(len(dict['hrs']), 'data points')

#  print('\nSubstations:', dict['keys_s'])
#  print('  Variables:', dict['idx_s'])

#  print('\nMeters:', dict['keys_m'])
#  print('  Variables:', dict['idx_m'])

#  print('\nInverters:', dict['keys_i'])
#  print('  Variables:', dict['idx_i'])

  indices = {}
  for tbl in ['keys_s', 'keys_m', 'keys_i']:
    i = 0
    for key in dict[tbl]:
      indices[key] = i
      i = i + 1
#  print (indices)

  data_m = dict['data_m']
  idx_m = dict['idx_m']
  print ('Meter Name         Bill     Energy    Vmax    Vmin HrsOut HrsBLO HrsALO')
  for key in meters:
    i = indices[key]
    bill = data_m[i,-1,idx_m['MTR_BILL_IDX']]
    energy = 0.001 * np.sum(data_m[i,:,idx_m['MTR_REAL_ENERGY_IDX']])
    max_v = np.amax(data_m[i,:,idx_m['MTR_VOLT_MAX_IDX']])
    min_v = np.amin(data_m[i,:,idx_m['MTR_VOLT_MIN_IDX']])
    dur_out = np.sum(data_m[i,:,idx_m['MTR_OUT_DURATION_IDX']]) / 3600.0
    dur_alo = np.sum(data_m[i,:,idx_m['MTR_ALO_DURATION_IDX']]) / 3600.0
    dur_blo = np.sum(data_m[i,:,idx_m['MTR_BLO_DURATION_IDX']]) / 3600.0
    print ('{:12s} {:10.2f} {:10.2f} {:6.4f} {:6.4f} {:6.2f} {:6.2f} {:6.2f}'.format (key, bill, energy, max_v, min_v, dur_out, dur_blo, dur_alo))
  # calculate the energy to homes in the last five days
  npts = len(dict['hrs'])
  istart = int(2 * npts / 7)
  home_kwh = np.zeros(npts, dtype=float)
  for key in ['homes_mtr_A', 'homes_mtr_B', 'homes_mtr_C']:
    i = indices[key]
    e = 0.001 * data_m[i,:,idx_m['MTR_REAL_ENERGY_IDX']]
    home_kwh += e
  energy = np.sum(home_kwh[istart:])
  print ('Home kWH = {:.2f} over points {:d} to {:d}'.format(energy, istart, npts))

  return indices

def plot_custom (dict, indices, save_file=None, save_only=False):
  hrs = dict['hrs']
  data_m = dict['data_m']
  keys_m = dict['keys_m']
  idx_m = dict['idx_m']

  # make a publication-quality plot
  lsize = 12
  asize = 16
  tsize = 20
  plt.rc('font', family='serif')
  plt.rc('xtick', labelsize=lsize)
  plt.rc('ytick', labelsize=lsize)
  plt.rc('axes', labelsize=asize)
  plt.rc('legend', fontsize=asize)
  pWidth = 15.0
  pHeight = 1.5 * pWidth / 1.618
  fig, ax = plt.subplots(2, 2, figsize=(pWidth, pHeight), sharex='col', constrained_layout=True)

  idx = idx_m['MTR_REAL_POWER_AVG_IDX']
  # Loads
  load_kw = np.zeros(len(hrs), dtype=float)
  for key in ['hub_mtr', 'homes_mtr_A', 'homes_mtr_B', 'homes_mtr_C']:
    i = indices[key]
    p = 0.001 * data_m[i,:,idx]
    load_kw += p
    ax[0,0].plot(hrs, p, label=key)
  ax[0,0].set_title('Load Power', fontsize=tsize)
  ax[0,0].set_ylabel('[kW]')
  ax[0,0].legend(loc='best')

  # DER
  for key in ['hub_pv_mtr', 'hub_bess_mtr', 'hub_dg_mtr']:
    i = indices[key]
    ax[0,1].plot(hrs, 0.001 * data_m[i,:,idx], label=key)
  ax[0,1].set_title('DER Power', fontsize=tsize)
  ax[0,1].set_ylabel('[kW]')
  ax[0,1].legend(loc='best')

  # Utility and gross power
  ax[1,0].plot(hrs, 0.001 * data_m[indices['fdr_head'],:,idx], label='Utility')
  ax[1,0].plot(hrs, load_kw, label='Load')
  ax[1,0].set_title('Utility and Gross Load Power', fontsize=tsize)
  ax[1,0].set_ylabel('[kW]')
  ax[1,0].legend(loc='best')

  # voltages
  idx = idx_m['MTR_VOLT_AVG_IDX']
  # Loads
  for key in ['hub_mtr', 'homes_mtr_A', 'homes_mtr_B', 'homes_mtr_C']:
    i = indices[key]
    ax[1,1].plot(hrs, data_m[i,:,idx], label=key)
  ax[1,1].set_title('Load Voltage', fontsize=tsize)
  ax[1,1].set_ylabel('[%]')
  ax[1,1].legend(loc='best')

  for i in range(2):
    for j in range(2):
      ax[i,j].grid()
      ax[i,j].set_xlim(tticks[0],tticks[-1])
      ax[i,j].set_xticks(tticks)
  for j in range(2):
    ax[1,j].set_xlabel('Hours')

  if save_file is not None:
    plt.savefig(save_file)
  if not save_only:
    plt.show()

def plot_hub (dict, indices, save_file=None, save_only=False):
  hrs = dict['hrs']
  data_m = dict['data_m']
  keys_m = dict['keys_m']
  idx_m = dict['idx_m']

  # make a publication-quality plot
  lsize = 18
  asize = 22
  tsize = 26
  plt.rc('font', family='serif')
  plt.rc('xtick', labelsize=lsize)
  plt.rc('ytick', labelsize=lsize)
  plt.rc('axes', labelsize=asize)
  plt.rc('legend', fontsize=asize)
  pWidth = 15.0
  pHeight = pWidth / 1.618
  fig, ax = plt.subplots(1, 1, figsize=(pWidth, pHeight), sharex='col', constrained_layout=True)

  idx = idx_m['MTR_REAL_POWER_AVG_IDX']
  ax.plot(hrs, 0.001 * data_m[indices['hub_mtr'],:,idx], label='Load', color='black')
  ax.plot(hrs, 0.001 * data_m[indices['hub_pv_mtr'],:,idx], label='PV', color='blue')
  ax.plot(hrs, 0.001 * data_m[indices['hub_bess_mtr'],:,idx], label='BESS', color='green')
  ax.plot(hrs, 0.001 * data_m[indices['hub_dg_mtr'],:,idx], label='DG', color='red')
  ax.set_title('Real Power at Hub', fontsize=tsize)
  ax.set_ylabel('[kW]')
  ax.legend(loc='best')
  ax.grid()
  ax.set_xlim(tticks[0],tticks[-1])
  ax.set_xticks(tticks)
  ax.set_xlabel('Hours')

  if save_file is not None:
    plt.savefig(save_file)
  if not save_only:
    plt.show()

def plot_meters (dict, save_file=None, save_only=False):
  hrs = dict['hrs']
  data_m = dict['data_m']
  keys_m = dict['keys_m']
  idx_m = dict['idx_m']
  fig, ax = plt.subplots(1, 1, sharex = 'col')
  i = 0
  for key in keys_m:
    ax.plot(hrs, 0.001 * data_m[i,:,idx_m['MTR_REAL_POWER_AVG_IDX']], label=key)
#    ax[1].plot(hrs, 0.001 * data_m[i,:,idx_m['MTR_REACTIVE_POWER_AVG_IDX']], label=key)
    i = i + 1
  ax.set_ylabel('Real Power [kW]')
#  ax[1].set_ylabel('Reactive Power [kvar]')
  ax.set_xlabel('Hours')
  ax.set_title ('Real Power at {:d} Meters'.format(len(keys_m)))
  ax.legend(loc='best')
  if save_file is not None:
    plt.savefig(save_file)
  if not save_only:
    plt.show()

rootname = 'soco_test'
if len(sys.argv) > 1:
  rootname = sys.argv[1]

gmetrics = gp.read_gld_metrics (rootname, 'soco_test_glm_dict.json')
indices = summarize_metrics (gmetrics)
#gp.plot_gld (gmetrics)
#vp.plot_voltages (gmetrics)
#plot_meters (gmetrics)
#plot_custom (gmetrics, indices, save_file='{:s}.png'.format(rootname))
plot_hub (gmetrics, indices, save_file='{:s}_hub.png'.format(rootname))

