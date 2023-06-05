import sys
import os
import math
import subprocess

# some data and utilities from CIMHub/BES/mpow.py

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

# sample code from TESP that automates Matpower in Octave
# https://github.com/pnnl/tesp/blob/develop/examples/capabilities/ercot/case8/tso_most.py

if sys.platform == 'win32':
  octave = '"C:\Program Files\GNU Octave\Octave-8.2.0\octave-launch.exe" --no-gui'
else:
  octave = 'octave'

def write_solve_file (root, load_scale):
  fname = 'solve{:s}.m'.format(root)
  fp = open (fname, 'w')
  print ("""clear;""", file=fp)
  print ("""cd {:s}""".format (os.getcwd()), file=fp)
  print ("""mpc = loadcase({:s});""".format (root.upper()), file=fp)
  print ("""# case_info(mpc);""", file=fp)
  print ("""mpc = scale_load({:.5f},mpc);""".format (load_scale), file=fp)
  print ("""opt1 = mpoption('out.all', 0, 'verbose', 0);""", file=fp)
  print ("""results=runpf(mpc, opt1);""", file=fp)
  print ("""define_constants;""", file=fp)
  print ("""codes=matpower_gen_type(results.gentype);""", file=fp)
  print ("""mg=[results.gen(:,GEN_BUS),results.gen(:,PG),results.gen(:,QG),codes];""", file=fp)
  print ("""mb=[results.bus(:,VM),results.bus(:,VA)];""", file=fp)
  print ("""csvwrite('{:s}mg.txt',mg);""".format (root.lower()), file=fp)
  print ("""csvwrite('{:s}mb.txt',mb);""".format (root.lower()), file=fp)
  print ("""exit;""", file=fp)
  fp.close()
  return fname

if __name__ == '__main__':
  case_id = 0
  if len(sys.argv) > 1:
    case_id = int(sys.argv[1])
  sys_name = CASES[case_id]['name']
  load_scale = CASES[case_id]['load_scale']
  fname = write_solve_file (sys_name, load_scale)
  cmdline = '{:s} {:s}'.format(octave, fname)
  print ('running', cmdline)
  proc = subprocess.Popen(cmdline, shell=True)
  proc.wait()

