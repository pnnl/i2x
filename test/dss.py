import i2x.api as i2x

if __name__ == "__main__":
#  doc_fp = open ('interface_functions.txt', 'w')
# dict = i2x.test_opendss_interface(choice = 'ieee9500',
#                                   pvcurve = 'pcloud',
#                                   invmode = 'CONSTANTPF',
#                                   loadmult = 0.5,
#                                   loadcurve = 'DEFAULT',
#                                   stepsize = 300,
#                                   numsteps = 288,
#                                   solnmode = 'DAILY',
#                                   ctrlmode = 'STATIC',
#                                   doc_fp=None)

  dict = i2x.test_opendss_interface(choice = 'ieee_lvn', 
                                    pvcurve = 'pclear', 
                                    invmode = 'CONSTANTPF', 
                                    loadmult = 1.0, 
                                    loadcurve = 'FLAT',
                                    stepsize = 300, 
                                    numsteps = 288,
                                    solnmode = 'DAILY',
                                    ctrlmode = 'STATIC',
                                    doc_fp=None)
#  print (dict)
#  doc_fp.close()

