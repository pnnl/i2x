# Copyright (C) 2020-2023 Battelle Memorial Institute
# file: mpow_utilities.py
# reads MATPOWER and MOST cases/results into Python

# sample code from TESP that automates Matpower in Octave
# https://github.com/pnnl/tesp/blob/develop/examples/capabilities/ercot/case8/tso_most.py

import numpy as np
import subprocess
import sys
import os
import math

# Matpower column numbers

# mpc.bus
BUS_I   =1-1
BUS_TYPE=2-1 # (1 = PQ, 2 = PV, 3 = ref, 4 = isolated)
PD=      3-1
QD=      4-1
GS=      5-1
BS=      6-1
BUS=AREA=7-1
VM=      8-1
VA=      9-1
BASE_KV=10-1
ZONE=   11-1
VMAX=   12-1
VMIN=   13-1
LAM_P=  14-1
LAM_Q=  15-1
MU_VMAX=16-1
MU_VMIN=17-1

#mpc.gen
GEN_BUS=   1-1
PG=        2-1
QG=        3-1
QMAX=      4-1
QMIN=      5-1
VG=        6-1
MBASE=     7-1
GEN_STATUS=8-1 # (>0 in-service, <= 0 out-of-service)
PMAX=      9-1
PMIN=     10-1
PC1=      11-1
PC2=      12-1
QC1MIN=   13-1
QC1MAX=   14-1
QC2MIN=   15-1
QC2MAX=   16-1
RAMP_AGC= 17-1
RAMP_10=  18-1
RAMP_30=  19-1
RAMP_Q=   20-1
APF=      21-1
MU_PMAX=  22-1
MU_PMIN=  23-1 
MU_QMAX=  24-1
MU_QMIN=  25-1

#mpc.branch
F_BUS=     1-1
T_BUS=     2-1
BR_R=      3-1
BR_X=      4-1
BR_B=      5-1
RATE_A=    6-1
RATE_B=    7-1
RATE_C=    8-1
TAP=       9-1 # (0 for line, Vfrom/Vt for transformer)
SHIFT=    10-1 # positive for delay, in degrees
BR_STATUS=11-1
ANGMIN=   12-1
ANGMAX=   13-1
PF=       14-1
QF=       15-1
PT=       16-1
QT=       17-1
MU_SF=    18-1
MU_ST=    19-1
MU_ANGMIN=20-1
MU_ANGMAX=21-1

#mpc.gencost
MODEL=   1-1 # 1 = piecewise linear, 2 = polynomial
STARTUP= 2-1 
SHUTDOWN=3-1
NCOST=   4-1 # number of data points or coefficients
COST=    5-1 # coordinates or coefficients

#mpc.dcline
DCL_F_BUS=    1-1
DCL_T_BUS=    2-1
DCL_BR_STATUS=3-1 #1 = in-service, 0 = out-of-service
DCL_PF=       4-1
DCL_PT=       5-1
DCL_QF=       6-1
DCL_QT=       7-1
DCL_VF=       8-1
DCL_VT=       9-1
DCL_PMIN=    10-1
DCL_PMAX=    11-1
DCL_QMINF=   12-1
DCL_QMAXF=   13-1
DCL_QMINT=   14-1
DCL_QMAXT=   15-1
DCL_LOSS0=   16-1
DCL_LOSS1=   17-1
DCL_MU_PMIN= 18-1
DCL_MU_PMAX= 19-1
DCL_MU_QMINF=20-1
DCL_MU_QMAXF=21-1
DCL_MU_QMINT=22-1
DCL_MU_QMAXT=23-1

# Table 3 of the APEN paper shows 2442.2 wind at bus 3, but the text gives correct value of 2242.2
ercot8_wind_plants = np.array ([1674.8, 2242.2, 8730.3, 99.8, 3562.2])
ercot8_wind_plant_buses = [1, 3, 4, 6, 7]
ercot8_wind_plant_rows = [14, 15, 16, 17, 18]
ercot8_load_rows = [1, 2, 3, 4, 5, 6, 7, 8]

# read the LARIMA model profiles from a data file, col0=hour, col1..n=MW output
def ercot_wind_profile (fname, start, end):
  wind = []
  np.set_printoptions(precision=3)
  dat = np.loadtxt (fname, delimiter=',')
  nwindpoints = np.shape(dat)[0]
  if end > nwindpoints:
    print ('ERROR: requested last hour={:d} is more than available wind hours={:d}'.format(end, nwindpoints))
    print ('Modify and run wind_plants.py to create enough synthetic wind data')
  else:
    wind = np.transpose(dat[start:end,1:])
    print ('Wind data shape', np.shape(dat), 'transformed to', np.shape(wind))
  return wind

# archived load data from TESP example of ERCOT8
ercot8_base_load = np.array ([[7182.65, 6831.0, 6728.83, 6781.1, 6985.44, 7291.94, 7650.72, 8104.54, 8522.71, 8874.36, 9173.74, 9446.98, 9736.85, 10078.99, 10466.28, 10855.94, 11179.08, 11319.26, 11200.46, 10893.96, 10630.22, 10326.1, 9781.99, 8810.21],
[7726.69, 6840.09, 6637.09, 6603.94, 6719.95, 6972.67, 7295.82, 7693.55, 8140.99, 8518.01, 8837.02, 9114.6, 9383.9, 9686.33, 10046.77, 10436.22, 10800.8, 11053.52, 11078.38, 10862.95, 10560.51, 10311.93, 9930.77, 9255.46],
[162.23, 150.74, 147.38, 147.58, 151.14, 157.34, 164.74, 174.24, 183.88, 191.86, 198.73, 204.8, 210.94, 218.0, 226.31, 234.89, 242.62, 247.1, 246.18, 240.24, 233.97, 228.03, 218.06, 200.84],
[2097.83, 1715.67, 1634.79, 1612.55, 1625.69, 1676.24, 1750.04, 1836.99, 1946.17, 2045.25, 2129.17, 2200.95, 2265.65, 2335.41, 2418.31, 2511.32, 2604.34, 2680.16, 2712.51, 2681.17, 2608.38, 2544.69, 2470.88, 2337.43],
[3922.54, 3492.58, 3390.92, 3376.09, 3437.51, 3568.83, 3731.92, 3937.36, 4163.99, 4356.73, 4519.81, 4661.72, 4801.51, 4956.12, 5140.39, 5337.36, 5523.74, 5650.82, 5663.53, 5549.16, 5396.66, 5267.47, 5070.49, 4723.14],
[232.03, 198.01, 191.14, 189.66, 192.44, 199.23, 208.37, 219.33, 232.2, 243.34, 252.82, 260.91, 268.66, 277.18, 287.27, 298.32, 309.02, 316.94, 318.77, 313.37, 304.59, 297.45, 287.36, 269.27],
[2650.16, 2535.62, 2503.87, 2529.95, 2610.47, 2727.27, 2864.48, 3034.58, 3187.67, 3315.82, 3425.81, 3527.87, 3636.74, 3766.01, 3911.17, 4055.18, 4170.85, 4212.81, 4159.51, 4043.84, 3947.45, 3827.25, 3612.92, 3213.76],
[56.55, 51.95, 50.65, 50.57, 51.68, 53.72, 56.25, 59.4, 62.76, 65.57, 67.97, 70.06, 72.15, 74.53, 77.34, 80.29, 83.0, 84.73, 84.61, 82.72, 80.5, 78.53, 75.32, 69.74]])

def run_matpower_and_wait (fscript, quiet=False):
  if sys.platform == 'win32':
    octave = '"C:\Program Files\GNU Octave\Octave-8.2.0\octave-launch.exe" --no-gui'
  else:
    octave = 'octave --no-window-system --no-gui >octave.log 2>&1 '
  cmdline = '{:s} {:s}'.format(octave, fscript)
  if not quiet:
    print ('running', cmdline)
  proc = subprocess.Popen(cmdline, shell=True)
  proc.wait()

# some data and utilities from CIMHub/BES/mpow.py

FUELS = {
  'hydro':  {'c2':1.0e-5, 'c1': 1.29, 'c0': 0.0},
  'wind':   {'c2':1.0e-5, 'c1': 0.01, 'c0': 0.0},
  'solar':  {'c2':1.0e-5, 'c1': 0.01, 'c0': 0.0},
  'coal':   {'c2':0.0009, 'c1': 19.0, 'c0': 2128.0},
  'ng':     {'c2':0.0060, 'c1': 45.0, 'c0': 2230.0},
  'nuclear':{'c2':0.00019, 'c1': 8.0, 'c0': 1250.0}
}

# global constants
SQRT3 = math.sqrt(3.0)
RAD_TO_DEG = 180.0 / math.pi
MVA_BASE = 100.0

def get_gencosts(fuel):
  c2 = 0.0
  c1 = 0.0
  c0 = 0.0
  if fuel in FUELS:
    c2 = FUELS[fuel]['c2']
    c1 = FUELS[fuel]['c1']
    c0 = FUELS[fuel]['c0']
  return c2, c1, c0

###################################################
# from tesp_support package, parse_msout.py

def next_val(fp, var, bInteger=True):
  match = '# name: ' + var
  looking = True
  val = None
  while looking:
    ln = fp.readline()
    if len(ln) < 1:
      print('EOF looking for', var)
      return val
    if ln.strip() == match:
      looking = False
      fp.readline()
      if bInteger:
        val = int(fp.readline().strip())
      else:
        val = float(fp.readline().strip())
  # print(var, '=', val)
  return val

def next_matrix(fp, var):
  match = '# name: ' + var
  looking = True
  mat = None
  while looking:
    ln = fp.readline()
    if len(ln) < 1:
      print('EOF looking for', var)
      return mat
    if ln.strip() == match:
      looking = False
      toks = fp.readline().strip().split()
      if toks[2] != 'matrix':
        print ('variable {:s} has invalid type {:s} in next_matrix'.format (var, toks[2]))
        return None
      toks = fp.readline().strip().split()
      if toks[1] == 'rows:': # a 2x2 matrix
        rows = int(toks[2])
        toks = fp.readline().strip().split()
        cols = int(toks[2])
        # print ('{:s} [{:d}x{:d}]'.format (var, rows, cols))
        mat = np.empty((rows, cols))
        for i in range(rows):
          mat[i] = np.fromstring(fp.readline().strip(), sep=' ')
      elif toks[1] == 'ndims:': # a generalized matrix
        ndims = int(toks[2])
        toks = fp.readline().strip().split()
        dims=tuple([int(i) for i in toks])
        nvals = 1
        for i in range (ndims):
          nvals *= dims[i]
#        print ('variable {:s} has ndims={:d} and dimension {:s} in next_matrix, reading {:d} elements'.format (var, ndims, str(dims), nvals))
        vals = np.empty (nvals)
        for i in range (nvals):
          vals[i] = np.fromstring(fp.readline().strip(), sep=' ')
        mat = np.reshape (vals, dims, order='F')

  return mat

def read_most_solution(fname='msout.txt'):
  fp = open(fname, 'r')

  f = next_val(fp, 'f', False)
  nb = next_val(fp, 'nb')
  ng = next_val(fp, 'ng')
  nl = next_val(fp, 'nl')
  ns = next_val(fp, 'ns')
  nt = next_val(fp, 'nt')
  nj_max = next_val(fp, 'nj_max')
  nc_max = next_val(fp, 'nc_max')
  psi = next_matrix(fp, 'psi')
  Pg = next_matrix(fp, 'Pg')
  Pd = next_matrix(fp, 'Pd')
  Rup = next_matrix(fp, 'Rup')
  Rdn = next_matrix(fp, 'Rdn')
  SoC = next_matrix(fp, 'SoC')
  Pf = next_matrix(fp, 'Pf')
  u = next_matrix(fp, 'u')
  lamP = next_matrix(fp, 'lamP')
  muF = next_matrix(fp, 'muF')
  fp.close()

  return f, nb, ng, nl, ns, nt, nj_max, nc_max, psi, Pg, Pd, Rup, Rdn, SoC, Pf, u, lamP, muF
###################################################

def read_matpower_array(fp, bStrings):
  A = []
  while True:
    ln = fp.readline()
    if '];' in ln:
      break
    if '};' in ln:
      break
    if ln[0] == '%':
      continue
    if ln[0] == '#':
      continue
    ln = ln.lstrip().rstrip(';\n')
    if bStrings:
      A.append(ln.strip("'"))
    else:
      A.append(ln.split())
  return A

def get_last_number (ln):
  toks = ln.split(' ')
  return toks[-1].strip('";\n')

def read_matpower_casefile(fname):
  d = {}
  fp = open(fname, 'r')
  while True:
    ln = fp.readline()
    if not ln:
      break
    if 'mpc.baseMVA' in ln:
      d['baseMVA'] = get_last_number (ln)
    elif 'mpc.version' in ln:
      d['version'] = get_last_number (ln)
    else:
      for table in ['gen', 'branch', 'bus', 'bus_name', 'gencost', 'gentype', 'genfuel']:
        token = 'mpc.{:s} ='.format(table)
        if token in ln:
          if table in ['gentype', 'genfuel']:
            bStrings = True
          else:
            bStrings = False
          d[table] = read_matpower_array(fp, bStrings)
  fp.close()
  return d

def write_matpower_string_vector (tag, d, fp):
  print ("""mpc.{:s} = {{""".format(tag), file=fp)
  for val in d:
    print ("""  '{:s}';""".format(val), file=fp)
  print ("""};""", file=fp)

def write_matpower_matrix (tag, d, fp):
  print ("""mpc.{:s} = [""".format(tag), file=fp)
  for row in d:
    line = ' '.join (['{:12.6f}'.format(float(x)) for x in row])
    print ("""  {:s};""".format(line), file=fp)
  print ("""];""", file=fp)

def write_matpower_casefile(d, fname):
  fp = open(fname+'.m', 'w')
  print ("""function mpc = {:s}""".format(fname), file=fp)
  print ("""mpc.version = "{:s}";""".format(d['version']), file=fp)
  print ("""mpc.baseMVA = {:.2f};""".format(float(d['baseMVA'])), file=fp)
  for tag in ['bus', 'gen', 'branch', 'gencost']:
    write_matpower_matrix (tag, d[tag], fp)
  for tag in ['gentype', 'genfuel']:
    write_matpower_string_vector (tag, d[tag], fp)
  fp.close()

def print_solution_summary (fname, details=False):
  fp = open(fname, 'r')
  converged = False
  iterations = 0
  time = 0.0
  for ln in fp.readlines():
    if 'results.success' in ln:
      if int(get_last_number(ln)) > 0:
        converged = True
    elif 'results.iterations' in ln:
      iterations = int(get_last_number(ln))
    elif 'results.et' in ln:
      time = float(get_last_number(ln))
    elif details:
      print (ln.strip('";\n'))
  print ('Converged: {:s} in {:d} iterations and {:.4f} seconds'.format(str(converged), iterations, time))
  fp.close()

def summarize_casefile (d, label):
  print ('Summary of {:s} data'.format (label))
  for key, val in d.items():
    if key in ['version', 'baseMVA']:
      print ('  {:s} = {:s}'.format(key, val))
    else:
      print ('  {:s} has {:d} rows'.format (key, len(val)))

def unit_color_label(genfuel):
  clr = 'orange'
  lbl = 'Solar'
  if genfuel == 'wind':
    clr = 'green'
    lbl = 'Wind'
  elif genfuel == 'nuclear':
    clr = 'red'
    lbl = 'Nuclear'
  elif genfuel == 'coal':
    clr = 'black'
    lbl = 'Coal'
  elif genfuel == 'ng':
    clr = 'blue'
    lbl = 'Gas'
  elif genfuel == 'dl':
    clr = 'magenta'
    lbl = 'Resp Load'
  return clr, lbl

def write_most_table_indices(fp):
  print("""  [PQ, PV, REF, NONE, BUS_I, BUS_TYPE, PD, QD, GS, BS, BUS_AREA, VM, ...
    VA, BASE_KV, ZONE, VMAX, VMIN, LAM_P, LAM_Q, MU_VMAX, MU_VMIN] = idx_bus;
  [F_BUS, T_BUS, BR_R, BR_X, BR_B, RATE_A, RATE_B, RATE_C, TAP, SHIFT, ...
    BR_STATUS, ANGMIN, ANGMAX, PF, QF, PT, QT, MU_SF, MU_ST, MU_ANGMIN, ...
    MU_ANGMAX] = idx_brch;
  [CT_LABEL, CT_PROB, CT_TABLE, CT_TBUS, CT_TGEN, CT_TBRCH, CT_TAREABUS, ...
    CT_TAREAGEN, CT_TAREABRCH, CT_ROW, CT_COL, CT_CHGTYPE, CT_REP, ...
    CT_REL, CT_ADD, CT_NEWVAL, CT_TLOAD, CT_TAREALOAD, CT_LOAD_ALL_PQ, ...
    CT_LOAD_FIX_PQ, CT_LOAD_DIS_PQ, CT_LOAD_ALL_P, CT_LOAD_FIX_P, ...
    CT_LOAD_DIS_P, CT_TGENCOST, CT_TAREAGENCOST, CT_MODCOST_F, ...
    CT_MODCOST_X] = idx_ct;
  [GEN_BUS, PG, QG, QMAX, QMIN, VG, MBASE, GEN_STATUS, PMAX, PMIN, ...
    MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN, PC1, PC2, QC1MIN, QC1MAX, ...
    QC2MIN, QC2MAX, RAMP_AGC, RAMP_10, RAMP_30, RAMP_Q, APF] = idx_gen;
  [PW_LINEAR, POLYNOMIAL, MODEL, STARTUP, SHUTDOWN, NCOST, COST] = idx_cost;""", file=fp)

def write_unresponsive_load_profile (root, rows, data, scale):
  fp = open('{:s}.m'.format(root), 'w')
  print('function unresp = {:s}'.format(root), file=fp)
  write_most_table_indices(fp)
  print("""  unresp = struct( ...
    'type', 'mpcData', ...
    'table', CT_TBUS, ...
    'rows', {:s}, ...
    'col', PD, ...
    'chgtype', CT_REP, ...
    'values', [] );""".format(str(rows)), file=fp)
  print('  scale = {:.3f};'.format(scale), file=fp)
  for i in range(len(rows)):
    rownum = rows[i]
    vals = str([round(v, 2) for v in data[i,:]])
    mvals = vals.replace(',', ';')
    print("""  unresp.values(:, 1, {:d}) = scale * {:s};""".format(rownum, mvals), file=fp)
  print('end', file=fp)
  fp.close()

def write_responsive_load_profile (root, rows, data, scale, fixed_root):
  fp = open('{:s}.m'.format(root), 'w')
  print('function resp = {:s}'.format(root), file=fp)
  write_most_table_indices(fp)
  print("""  resp = struct( ...
    'type', 'mpcData', ...
    'table', CT_TLOAD, ...
    'rows', {:s}, ...
    'col', CT_LOAD_DIS_P, ...
    'chgtype', CT_REP, ...
    'values', [] );""".format(str(rows)), file=fp)
  print('  scale = {:.3f};'.format(scale), file=fp)
  for i in range(len(rows)):
    rownum = rows[i]
    vals = str([round(v, 2) for v in data[i,:]])
    mvals = vals.replace(',', ';')
    print("""  resp.values(:, 1, {:d}) = scale * {:s};""".format(rownum, mvals), file=fp)
  print("""
  # per answer to https://github.com/MATPOWER/matpower/issues/106
  #   apply scaling to the total of responsive plus unresponsive load
  unresp = {:s};
  resp.values = resp.values + unresp.values;""".format(fixed_root), file=fp)
  print('end', file=fp)
  fp.close()

def write_wind_profile (root, rows, data):
  fp = open('{:s}.m'.format(root), 'w')
  print('function wind = {:s}'.format(root), file=fp)
  write_most_table_indices(fp)
  print("""  wind = struct( ...
    'type', 'mpcData', ...
    'table', CT_TGEN, ...
    'rows', {:s}, ...
    'col', PMAX, ...
    'chgtype', CT_REP, ...
    'values', [] );""".format(str(rows)), file=fp)
  for i in range(len(rows)):
    vals = str([round(v, 2) for v in data[i,:]])
    mvals = vals.replace(',', ';')
    print("""  wind.values(:, 1, {:d}) = {:s};""".format(i+1, mvals), file=fp)
  print('end', file=fp)
  fp.close()

def write_contab (root, d, scales):
  br = d['branch']
  fname = '{:s}.m'.format(root)
  fp = open(fname, 'w')
  print('function chgtab = {:s}'.format(root), file=fp)
  write_most_table_indices(fp)
  print('  %	label	prob	table	row	col	chgtype	newval', file=fp)
#  1	0	CT_TBRCH	1	BR_STATUS	CT_REP	0;
  print('  chgtab = [', file=fp)
  n = 0
  prob = 1.0
  label = 1
  for key, val in scales.items():
    idx = int(key)
    if val > 0.0:
      r = float(br[idx-1][BR_R]) / val
      x = float(br[idx-1][BR_X]) / val
      b = float(br[idx-1][BR_B]) * val
      sa = float(br[idx-1][RATE_A]) * val
      sb = float(br[idx-1][RATE_B]) * val
      sc = float(br[idx-1][RATE_C]) * val
      n += 6
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} BR_R      CT_REP {:11.7f};'.format (label, prob, idx, r), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} BR_X      CT_REP {:11.7f};'.format (label, prob, idx, x), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} BR_B      CT_REP {:11.5f};'.format (label, prob, idx, b), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} RATE_A    CT_REP {:11.3f};'.format (label, prob, idx, sa), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} RATE_B    CT_REP {:11.3f};'.format (label, prob, idx, sb), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} RATE_C    CT_REP {:11.3f};'.format (label, prob, idx, sc), file=fp)
    else:
      n += 1
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} BR_STATUS CT_REP         0.0;'.format (label, prob, idx), file=fp)
  print('  ];', file=fp)
  print('end', file=fp)
  fp.close()
# print ('wrote {:d} changes labeled {:d} to {:s}'.format (n, label, fname))

def write_contab_list (root, d, conts):
  br = d['branch']
  fname = '{:s}.m'.format(root)
  fp = open(fname, 'w')
  print('function chgtab = {:s}'.format(root), file=fp)
  write_most_table_indices(fp)
  print('  %	label	prob	table	row	col	chgtype	newval', file=fp)
#  1	0	CT_TBRCH	1	BR_STATUS	CT_REP	0;
  print('  chgtab = [', file=fp)
  n = len(conts)
  prob = 0.5 / n # contingencies combine for 50% of the probability
  prob = 1.0 / (n+1.0)  # contingencies and base case all weighted equally
  for i in range(n):
    label = i+1
    idx = conts[i]['branch']
    val = conts[i]['scale']
    if val > 0.0:
      r = float(br[idx-1][BR_R]) / val
      x = float(br[idx-1][BR_X]) / val
      b = float(br[idx-1][BR_B]) * val
      sa = float(br[idx-1][RATE_A]) * val
      sb = float(br[idx-1][RATE_B]) * val
      sc = float(br[idx-1][RATE_C]) * val
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} BR_R      CT_REP {:11.7f};'.format (label, prob, idx, r), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} BR_X      CT_REP {:11.7f};'.format (label, prob, idx, x), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} BR_B      CT_REP {:11.5f};'.format (label, prob, idx, b), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} RATE_A    CT_REP {:11.3f};'.format (label, prob, idx, sa), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} RATE_B    CT_REP {:11.3f};'.format (label, prob, idx, sb), file=fp)
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} RATE_C    CT_REP {:11.3f};'.format (label, prob, idx, sc), file=fp)
    else:
      print ('   {:3d} {:9.7f} CT_TBRCH {:3d} BR_STATUS CT_REP         0.0;'.format (label, prob, idx), file=fp)
  print('  ];', file=fp)
  print('end', file=fp)
  fp.close()
  print ('wrote {:d} labeled contingencies to {:s}'.format (n, fname))

# minup, mindown
def get_plant_min_up_down_hours(fuel, gencosts, gen):
  if fuel == 'nuclear':
    return 24, 24
  if fuel == 'coal':
    return 12, 12
  if fuel == 'ng':
    if float(gencosts[4]) < 57.0:
      return 6, 6
  return 1, 1

# paPrice, naPrice, pdPrice, ndPrice, plfPrice, nlfPrice
def get_plant_prices(fuel, gencosts, gen):
  return 0.001, 0.001, 0.001, 0.001, 0.1, 0.1

def get_plant_reserve(fuel, gencosts, gen):
  if len(fuel) < 1:
    return 10000.0
  if fuel == 'dl':
    return abs(float(gen[PMIN]))
  return abs(float(gen[PMAX]))

def get_plant_commit_key(fuel, gencosts, gen, use_wind):
  if len(fuel) > 0:
    if fuel == 'wind':
      if use_wind:
        return 1
      else:
        return -1
    elif fuel == 'dl':
      return 2
    else:
      return 1
  return 2

def write_xgd_function (root, gen, gencost, genfuel, unit_state, use_wind=True):
  fp = open('{:s}.m'.format(root), 'w')
  print("""function [xgd_table] = {:s} (mpc)
  xgd_table.colnames = {{
    'CommitKey', ...
    'InitialState',...
    'MinUp', ...
    'MinDown', ...
    'PositiveActiveReservePrice', ...
    'PositiveActiveReserveQuantity', ...
    'NegativeActiveReservePrice', ...
    'NegativeActiveReserveQuantity', ...
    'PositiveActiveDeltaPrice', ...
    'NegativeActiveDeltaPrice', ...
    'PositiveLoadFollowReservePrice', ...
    'PositiveLoadFollowReserveQuantity', ...
    'NegativeLoadFollowReservePrice', ...
    'NegativeLoadFollowReserveQuantity', ...
  }};
  xgd_table.data = [""".format(root), file=fp)
# print ('gen', gen)
# print ('gencost', gencost)
# print ('genfuel', genfuel)
# print ('unit_states', unit_state)
  ngen = 0
  nwind = 0
  nresp = 0
  for i in range(len(genfuel)):
    if genfuel[i] == 'wind':
      nwind += 1
    elif genfuel[i] == 'dl':
      nresp += 1
    else:
      ngen += 1
    commit = get_plant_commit_key(genfuel[i], gencost[i], gen[i], use_wind)
    reserve = get_plant_reserve(genfuel[i], gencost[i], gen[i])
    minup, mindown = get_plant_min_up_down_hours(genfuel[i], gencost[i], gen[i])
    paPrice, naPrice, pdPrice, ndPrice, plfPrice, nlfPrice = get_plant_prices(genfuel[i], gencost[i], gen[i])
    print(' {:2d} {:4d} {:2d} {:2d} {:f} {:.2f} {:f} {:.2f} {:f} {:f} {:f} {:.2f} {:f} {:.2f};'
        .format(commit, int(unit_state[i]), minup, mindown, paPrice, reserve, naPrice, reserve,
            pdPrice, ndPrice, plfPrice, reserve, nlfPrice, reserve), file=fp)
  print('];', file=fp)
  print('end', file=fp)
  fp.close()
  print ('configured {:d} generators, {:d} wind plants, {:d} responsive loads'.format(ngen, nwind, nresp))

def ercot_daily_loads (start, end, resp_scale):
  # pad the load profiles to cover requested number of hours
  fixed_load = ercot8_base_load
  while np.shape(fixed_load)[1] < end:
    fixed_load = np.hstack((fixed_load, ercot8_base_load))
    print ('  stacking load shapes to', np.shape(fixed_load))
  fixed_load = fixed_load[:,start:end]
  print ('using fixed load shape', np.shape(fixed_load))
  responsive_load = resp_scale * fixed_load
  return fixed_load, responsive_load

def write_hca_solve_file (root, solver='GLPK', load_scale=None, upgrades=None, cmd=None, quiet=False):
  fscript = 'solve_{:s}.m'.format(root)
  fsummary = '{:s}_summary.txt'.format(root)
  fp = open(fscript, 'w')
  print("""clear;""", file=fp)
  print("""define_constants;""", file=fp)
  print("""mpopt = mpoption('verbose', 0, 'out.all', 0);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.dc_model', 1);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.uc.run', 1);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.solver', '{:s}');""".format(solver), file=fp)
  if quiet:
    print("""mpopt = mpoption(mpopt, 'glpk.opts.msglev', 0);""", file=fp)
  else:
    print("""mpopt = mpoption(mpopt, 'glpk.opts.msglev', 1);""", file=fp)
  if upgrades is None:
    print("""mpc = loadcase ('{:s}_case.m');""".format(root), file=fp)
  else:
    print("""mpcbase = loadcase ('{:s}_case.m');""".format(root), file=fp)
    print("""upgrades = {:s};""".format(upgrades), file=fp)
    print("""mpc = apply_changes (1, mpcbase, upgrades);""", file=fp)
  if load_scale is not None:
    print ("""mpc = scale_load({:.5f},mpc);""".format (load_scale), file=fp)
  if cmd is not None:
    print (cmd, file=fp)
  print("""xgd = loadxgendata('{:s}_xgd.m', mpc);""".format(root), file=fp)
  print("""mdi = loadmd(mpc, [], xgd, [], '{:s}_contab.m');""".format(root), file=fp)
  print("""mdo = most(mdi, mpopt);""", file=fp)
  print("""ms = most_summary(mdo);""", file=fp)
  print("""save('-text', '{:s}', 'ms');""".format(fsummary), file=fp)
  if not quiet:
    print("""total_time = mdo.results.SolveTime + mdo.results.SetupTime""", file=fp)
  fp.close()
  return fscript, fsummary

def write_matpower_solve_file (root, load_scale): # this one is not used
  fscript = 'solve{:s}.m'.format(root)
  fsolved = '{:s}solved.m'.format(root)
  fsummary = '{:s}summary.txt'.format(root)
# fbus = '{:s}bus.txt'.format(root.lower())
# fgen = '{:s}gen.txt'.format(root.lower())
# fbranch = '{:s}branch.txt'.format(root.lower())
  fp = open (fscript, 'w')
  print ("""clear;""", file=fp)
  print ("""cd {:s}""".format (os.getcwd()), file=fp)
  print ("""mpc = loadcase({:s});""".format (root), file=fp)
# print ("""case_info(mpc);""", file=fp)
  print ("""mpc = scale_load({:.5f},mpc);""".format (load_scale), file=fp)
  print ("""opt1 = mpoption('out.all', 0, 'verbose', 0);""", file=fp)
  print ("""results=runpf(mpc, opt1);""", file=fp)
  print ("""define_constants;""", file=fp)
# print ("""codes=matpower_gen_type(results.gentype);""", file=fp)
# print ("""mgen=[results.gen(:,GEN_BUS),results.gen(:,PG),results.gen(:,QG),codes];""", file=fp)
# print ("""mbus=[results.bus(:,VM),results.bus(:,VA),results.bus(:,PD),results.bus(:,QD)];""", file=fp)
# print ("""mbranch=[results.branch(:,F_BUS),results.branch(:,T_BUS),results.branch(:,TAP),results.branch(:,SHIFT),results.branch(:,PF),results.branch(:,QF),results.branch(:,PT),results.branch(:,QT)];""", file=fp)
# print ("""csvwrite('{:s}',mgen);""".format (fgen), file=fp)
# print ("""csvwrite('{:s}',mbus);""".format (fbus), file=fp)
# print ("""csvwrite('{:s}',mbranch);""".format (fbranch), file=fp)
  print ("""opt2 = mpoption('out.sys_sum', 1, 'out.bus', 0, 'out.branch', 0);""", file=fp)
  print ("""fd = fopen('{:s}', 'w');""".format (fsummary), file=fp)
  print ("""fprintf(fd,'results.success = %d\\n', results.success);""", file=fp)
  print ("""fprintf(fd,'results.iterations = %d\\n', results.iterations);""", file=fp)
  print ("""fprintf(fd,'results.et = %.4f\\n', results.et);""", file=fp)
  print ("""printpf(results, fd, opt2);""", file=fp)
  print ("""fclose(fd);""", file=fp)
  print ("""savecase('{:s}', results);""".format (fsolved), file=fp)
  print ("""exit;""", file=fp)
  fp.close()
  return fscript, fsolved, fsummary

def write_most_solve_file (root, solver='GLPK', chgtab=None):
  fscript = 'solve_{:s}.m'.format(root)
  fsummary = '{:s}_summary.txt'.format(root)
  fp = open(fscript, 'w')
  print("""clear;""", file=fp)
  print("""define_constants;""", file=fp)
  print("""mpopt = mpoption('verbose', 0, 'out.all', 0);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.dc_model', 1);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.uc.run', 1);""", file=fp)
  print("""mpopt = mpoption(mpopt, 'most.solver', '{:s}');""".format(solver), file=fp)
  print("""mpopt = mpoption(mpopt, 'glpk.opts.msglev', 1);""", file=fp)
  if chgtab is None:
    print("""mpc = loadcase ('{:s}_case.m');""".format(root), file=fp)
  else:
    print("""mpcbase = loadcase ('{:s}_case.m');""".format(root), file=fp)
    print("""chgtab = {:s};""".format(chgtab), file=fp)
    print("""mpc = apply_changes (1, mpcbase, chgtab);""", file=fp)
  print("""xgd = loadxgendata('{:s}_xgd.m', mpc);""".format(root), file=fp)
  print("""profiles = getprofiles('{:s}_unresp.m');""".format(root), file=fp)
  print("""profiles = getprofiles('{:s}_resp.m', profiles);""".format(root), file=fp)
  print("""profiles = getprofiles('{:s}_wind.m', profiles);""".format(root), file=fp)
  print("""nt = size(profiles(1).values, 1);""", file=fp)
  print("""mdi = loadmd(mpc, nt, xgd, [], [], profiles);""", file=fp)
  print("""mdo = most(mdi, mpopt);""", file=fp)
  print("""ms = most_summary(mdo);""", file=fp)
  print("""save('-text', '{:s}', 'ms');""".format(fsummary), file=fp)
  print("""total_time = mdo.results.SolveTime + mdo.results.SetupTime""", file=fp)
  fp.close()
  return fscript, fsummary

def update_unit_state (old, row):
  hours_run = np.sum(row)
  retval = old
  if (hours_run > 23.5) and (old > 0.0):
    retval += 24.0
  elif (hours_run < 0.5) and (old < 0.0):
    retval -= 24.0
  else:  # the unit turned ON or OFF sometime during the day
    if row[-1] > 0.5:  # will end the day ON, how many hours will it have been ON?
      retval = 1
      for j in range(22, -1, -1):
        if row[j] > 0.0:
          retval += 1.0
        else:
          break
    else:  # will end the day OFF, how many hours will it have been OFF?
      retval = -1
      for j in range(22, -1, -1):
        if row[j] < 0.5:
          retval -= 1
        else:
          break
  return retval

def write_most_summary (d, lamP, Pf, muF, unit_states, u, show_hours_run=False):
  bus = d['bus']
  nb = len(bus)
  print ('Bus Summary')
  print ('Idx  MaxLMP  AvgLMP')
  for i in range (nb):
    print ('{:3d} {:7.2f} {:7.2f}'.format(i+1, np.max(lamP[i,:]), np.mean(lamP[i,:])))

  br = d['branch']
  nl = len(br)
  print ('Branch Summary')
  print ('Idx Frm  To  Rating  PkFlow Avg muF')
  for i in range (nl):
    print ('{:3d} {:3d} {:3d} {:7.1f} {:7.1f} {:7.2f}'.format(i+1, int(float(br[i][F_BUS])), int(float(br[i][T_BUS])), 
                                                            float(br[i][RATE_A]), np.max(np.abs(Pf[i,:])), 
                                                            np.mean(muF[i,:])))
  gen = d['gen']
  ng = len(gen)
  print ('Generator States')
  if show_hours_run:
    print ('Idx Bus Fuel    Now Ust Hrs')
    for i in range (ng):
      print ('{:3d} {:3d} {:7s} {:3d} {:3d} {:3d}'.format(i+1, int(float (gen[i][GEN_BUS])), d['genfuel'][i], 
                                                          int(u[i,-1]), int(unit_states[i]), int(np.sum(u[i]))))
  else:
    print ('Idx Bus Fuel    Now Ust History')
    for i in range (ng):
      print ('{:3d} {:3d} {:7s} {:3d} {:3d}'.format(i+1, int(float (gen[i][GEN_BUS])), d['genfuel'][i], int(u[i,-1]), int(unit_states[i])), u[i])

def concatenate_MOST_result (total, new):
  if total is None:
    total = new
  else:
    total = np.hstack ((total, new))
  return total
