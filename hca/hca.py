import i2x.api as i2x

def print_column_keys (label, d):
  columns = ''
  for key, row in d.items():
    columns = 'described by ' + str(row.keys())
    break
  print ('{:4d} {:20s} {:s}'.format (len(d), label, columns))

if __name__ == "__main__":
# dict = i2x.run_opendss(choice = 'ieee9500',
#                        pvcurve = 'pvduty', # 'pcloud',
#                        invmode = 'CONSTANT_PF', # 'VOLT_VAR_VOLT_WATT', # 'VOLT_WATT', # 'VOLT_VAR_AVR', # 'VOLT_VAR', #'CONSTANT_PF',
#                        invpf = 1.00,
#                        loadmult = 0.5,
#                        loadcurve = 'DEFAULT',
#                        stepsize = 1, # 300,
#                        numsteps = 2900, # 288,
#                        solnmode = 'DUTY', # 'DAILY',
#                        ctrlmode = 'STATIC')

# dict = i2x.run_opendss(choice = 'ieee_lvn',
#                        pvcurve = 'pclear',
#                        invmode = 'CONSTANT_PF',
#                        invpf = 1.00,
#                        loadmult = 1.0,
#                        loadcurve = 'FLAT',
#                        stepsize = 300,
#                        numsteps = 288,
#                        solnmode = 'DAILY', # 'SNAPSHOT',
#                        ctrlmode = 'STATIC')
# print (dict)
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
  pvder, gender, batder, largeder, resloads, loadkw = i2x.parse_opendss_graph(G, bSummarize=False)

  print ('\nLoaded Feeder Model {:s}'.format(feederName))
  print_column_keys ('Large DER', largeder)
  print_column_keys ('Generators', gender)
  print_column_keys ('PV DER', pvder)
  print_column_keys ('Batteries', batder)
  print_column_keys ('Rooftop Candidates', resloads)

