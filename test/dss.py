import i2x.api as i2x

if __name__ == "__main__":
#  doc_fp = open ('interface_functions.txt', 'w')
  dict = i2x.test_opendss_interface(choice = 'ieee9500',
                                    pvcurve = 'pvduty', # 'pcloud',
                                    invmode = 'CONSTANT_PF', # 'VOLT_VAR_VOLT_WATT', # 'VOLT_WATT', # 'VOLT_VAR_AVR', # 'VOLT_VAR', #'CONSTANT_PF',
                                    invpf = 1.00,
                                    loadmult = 0.5,
                                    loadcurve = 'DEFAULT',
                                    stepsize = 1, # 300,
                                    numsteps = 2900, # 288,
                                    solnmode = 'DUTY', # 'DAILY',
                                    ctrlmode = 'STATIC',
                                    doc_fp=None)

# dict = i2x.test_opendss_interface(choice = 'ieee_lvn',
#                                   pvcurve = 'pclear',
#                                   invmode = 'CONSTANT_PF',
#                                   invpf = 1.00,
#                                   loadmult = 1.0,
#                                   loadcurve = 'FLAT',
#                                   stepsize = 300,
#                                   numsteps = 288,
#                                   solnmode = 'DAILY',
#                                   ctrlmode = 'STATIC',
#                                   doc_fp=None)
#  print (dict)
#  doc_fp.close()

