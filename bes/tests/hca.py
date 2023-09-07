import sys
import numpy as np
import i2x.bes_hca as hca
import json
import time

if __name__ == '__main__':
  cfg_filename=None
  if len(sys.argv) > 1:
     cfg_filename = sys.argv[1]
  start = time.time()
  results = hca.bes_hca (cfg_filename= cfg_filename, log_output=True, write_json=True)
  print ('{:.2f} seconds elapsed'.format(time.time() - start))

