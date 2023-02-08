import i2x.api as i2x

if __name__ == "__main__":
#  doc_fp = open ('interface_functions.txt', 'w')
#  i2x.print_opendss_interface(doc_fp)
#  doc_fp.close()

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

  dict = i2x.run_opendss(choice = 'ieee_lvn',
                         pvcurve = 'pclear',
                         invmode = 'CONSTANT_PF',
                         invpf = 1.00,
                         loadmult = 1.0,
                         loadcurve = 'FLAT',
                         stepsize = 300,
                         numsteps = 288,
                         solnmode = 'DAILY', # 'SNAPSHOT',
                         ctrlmode = 'STATIC')
#  print (dict)

