import i2x.api as i2x

if __name__ == "__main__":
# doc_fp = open ('interface_functions.txt', 'w')
# i2x.print_opendss_interface(doc_fp)
# doc_fp.close()

  dict = i2x.run_opendss(choice = 'ieee9500',
                         pvcurve = 'pcloud', # 'pvduty', # 'pcloud',
                         invmode = 'VOLT_VAR_AVR', # 'VOLT_VAR_VOLT_WATT', 'VOLT_WATT', 'VOLT_VAR_AVR', 'VOLT_VAR_CATA', 'VOLT_VAR_CATB', 'CONSTANT_PF',
                         invpf = -0.90,
                         loadmult = 1.0,
                         loadcurve = 'qdaily',
                         stepsize = 300, # 1, 300,
                         numsteps = 288, # 2900, 288,
                         solnmode = 'DAILY', # 'DUTY', 'DAILY',
                         ctrlmode = 'STATIC')

  dict = i2x.run_opendss(choice = 'ieee_lvn',
                         pvcurve = 'pclear',
                         invmode = 'CONSTANT_PF',
                         invpf = 1.00,
                         loadmult = 1.0,
                         loadcurve = 'FLAT', # 'qdaily', 'FLAT',
                         stepsize = 300,
                         numsteps = 288,
                         solnmode = 'DAILY', # 'SNAPSHOT',
                         ctrlmode = 'STATIC')
  for tag in ['converged', 'num_cap_switches', 'num_tap_changes', 'num_relay_trips']:
    print ('  {:s}={:s}'.format (tag, str(dict[tag])))

