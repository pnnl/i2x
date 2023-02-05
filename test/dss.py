import i2x.api as i2x

if __name__ == "__main__":
#  doc_fp = open ('interface_functions.txt', 'w')
  dict = i2x.test_opendss_interface(choice = 'ieee9500', 
                                    pvcurve = 'pcloud', 
                                    loadmult = 0.5, 
                                    stepsize = 300, 
                                    numsteps = 288, 
                                    doc_fp=None)

  dict = i2x.test_opendss_interface(choice = 'ieee_lvn', 
                                    pvcurve = 'pclear', 
                                    loadmult = 1.0, 
                                    stepsize = 300, 
                                    numsteps = 288, 
                                    doc_fp=None)
#  print (dict)
#  doc_fp.close()

