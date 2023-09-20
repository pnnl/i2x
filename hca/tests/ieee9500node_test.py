import sys
import os
if os.path.abspath("..") not in sys.path:
    sys.path.append(os.path.abspath(".."))
import hca as h

### load config (note: just changes to defaults)
inputs = h.load_config("hca9500node_testconfig.json")

hca = h.HCA(inputs) # instantiate hca intance
hca.runbase()       # run baseline

### Perform 3 rounds of HCA
for i in range(3):
    hca.hca_round("pv")

# plot resulting feeder
hca.plot()