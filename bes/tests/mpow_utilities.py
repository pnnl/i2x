# Copyright (C) 2020-2023 Battelle Memorial Institute
# file: mpow_utilities.py
# reads MATPOWER and MOST cases/results into Python

import numpy as np

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
      fp.readline()
      toks = fp.readline().strip().split()
      rows = int(toks[2])
      toks = fp.readline().strip().split()
      cols = int(toks[2])
      # print ('{:s} [{:d}x{:d}]'.format (var, rows, cols))
      mat = np.empty((rows, cols))
      for i in range(rows):
        mat[i] = np.fromstring(fp.readline().strip(), sep=' ')
  return mat

def read_most_solution(fname='msout.txt'):
  fp = open('msout.txt', 'r')

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
  Pf = next_matrix(fp, 'Pf')
  u = next_matrix(fp, 'u')
  lamP = next_matrix(fp, 'lamP')
  muF = next_matrix(fp, 'muF')
  fp.close()

  return f, nb, ng, nl, ns, nt, nj_max, nc_max, Pg, Pd, Pf, u, lamP
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

