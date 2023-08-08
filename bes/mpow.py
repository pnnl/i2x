import sys
import os
import math
import subprocess
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

# some data from CIMHub/BES/mpow.py

CASES = [
  {'id': '1783D2A8-1204-4781-A0B4-7A73A2FA6038', 
   'name': 'IEEE118', 
   'swingbus':'131',
   'load_scale':0.6748},
  {'id': '2540AF5C-4F83-4C0F-9577-DEE8CC73BBB3', 
   'name': 'WECC240', 
   'swingbus':'2438',
   'load_scale':1.0425},
]

# global constants
SQRT3 = math.sqrt(3.0)
RAD_TO_DEG = 180.0 / math.pi
MVA_BASE = 100.0

def read_matpower_array(fp):
  A = []
  while True:
    ln = fp.readline()
    if '];' in ln:
      break
    if '};' in ln:
      break
    ln = ln.lstrip().rstrip(';\n')
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
          d[table] = read_matpower_array(fp)
  fp.close()
  return d

# sample code from TESP that automates Matpower in Octave
# https://github.com/pnnl/tesp/blob/develop/examples/capabilities/ercot/case8/tso_most.py

if sys.platform == 'win32':
  octave = '"C:\Program Files\GNU Octave\Octave-8.2.0\octave-launch.exe" --no-gui'
else:
  octave = 'octave --no-window-system --no-gui'

def write_solve_file (root, load_scale):
  fscript = 'solve{:s}.m'.format(root)
  fsolved = '{:s}solved.m'.format(root)
  fsummary = '{:s}summary.txt'.format(root)
# fbus = '{:s}bus.txt'.format(root.lower())
# fgen = '{:s}gen.txt'.format(root.lower())
# fbranch = '{:s}branch.txt'.format(root.lower())
  fp = open (fscript, 'w')
  print ("""clear;""", file=fp)
  print ("""cd {:s}""".format (os.getcwd()), file=fp)
  print ("""mpc = loadcase({:s});""".format (root.upper()), file=fp)
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

if __name__ == '__main__':
  case_id = 0
  if len(sys.argv) > 1:
    case_id = int(sys.argv[1])
  sys_name = CASES[case_id]['name']
  load_scale = CASES[case_id]['load_scale']
  d = read_matpower_casefile ('{:s}.m'.format (sys_name))
#  summarize_casefile (d, 'Input')
  fscript, fsolved, fsummary = write_solve_file (sys_name, load_scale)
  cmdline = '{:s} {:s}'.format(octave, fscript)
  print ('running', cmdline)
  proc = subprocess.Popen(cmdline, shell=True)
  proc.wait()
  print_solution_summary (fsummary, details=True)
  r = read_matpower_casefile (fsolved)
  for tag in ['bus', 'gen', 'branch', 'gencost']:
    r[tag] = np.array(r[tag], dtype=float)
#  summarize_casefile (r, 'Solved')
  print ('Min and max bus voltages=[{:.4f},{:.4f}]'.format (np.min(r['bus'][:,VM]),np.max(r['bus'][:,VM])))
  print ('Load = {:.3f} + j{:.3f} MVA'.format (np.sum(r['bus'][:,PD]),np.sum(r['bus'][:,QD])))
  print ('Gen =  {:.3f} + j{:.3f} MVA'.format (np.sum(r['gen'][:,PG]),np.sum(r['gen'][:,QG])))
  gen_online = np.array(r['gen'][:,GEN_STATUS]>0)
  print ('{:d} of {:d} generators on line'.format (int(np.sum(gen_online)),r['gen'].shape[0]))
  pgmax = np.sum(r['gen'][:,PMAX], where=gen_online)
  qgmax = np.sum(r['gen'][:,QMAX], where=gen_online)
  qgmin = np.sum(r['gen'][:,QMIN], where=gen_online)
  print ('Online capacity = {:.2f} MW, {:.2f} to {:.2f} MVAR'.format (pgmax, qgmin, qgmax))

