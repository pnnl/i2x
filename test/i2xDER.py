# Copyright (C) 2023 Battelle Memorial Institute
# file: i2xDER.py
"""Presents a GUI for DER boot camp
"""
import i2x.api as i2x

if __name__ == "__main__":
#  i2x.make_builtin_graph('ieee_lvn')
#  i2x.make_builtin_graph('ieee9500')
#  i2x.make_opendss_graph('../src/i2x/models/ieee9500/graph/', '../src/i2x/models/ieee9500/Network.json')
#  G = i2x.load_opendss_graph('../src/i2x/models/ieee9500/Network.json')
  G = i2x.load_builtin_graph('ieee_lvn')
  if G is not None:
    i2x.plot_opendss_feeder(G, plot_labels=True)
#  i2x.show_der_config()

