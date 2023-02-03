# Copyright (C) 2023 Battelle Memorial Institute
# file: der.py
"""Presents a GUI for DER boot camp
"""
import i2x.api as i2x

if __name__ == "__main__":
#  i2x.make_builtin_graph('ieee9500')
#  i2x.make_opendss_graph('../src/i2x/models/ieee9500/graph/', '../src/i2x/models/ieee9500/Network.json')
#  i2x.make_opendss_graph('../src/i2x/models/ieee_lvn/graph/', '../src/i2x/models/ieee_lvn/Network.json')
#  G = i2x.load_opendss_graph('../src/i2x/models/ieee9500/Network.json')
#  G = i2x.load_builtin_graph('ieee_lvn')
#  if G is not None:
#    i2x.plot_opendss_feeder(G)
  i2x.show_der_config()

