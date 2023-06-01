# Copyright (C) 2023 Battelle Memorial Institute
# file: i2xDER.py
"""Presents a GUI for DER boot camp
"""
import i2x.api as i2x

import matplotlib.pyplot as plt
import os
plt.rcParams['savefig.directory'] = '../docs/media' # os.getcwd()

if __name__ == "__main__":
#  i2x.make_opendss_graph(saved_path='../src/i2x/models/ieee9500/graph/',
#                         outfile='../src/i2x/models/ieee9500/Network.json',
#                         extra_source_buses=['hvmv69sub1_hsb', 'hvmv69sub2_hsb', 'hvmv69sub3_hsb'])
#  i2x.make_opendss_graph(saved_path='../src/i2x/models/ieee_lvn/graph/',
#                         outfile='../src/i2x/models/ieee_lvn/Network.json',
#                         extra_source_buses=[])
#  G = i2x.load_opendss_graph('../src/i2x/models/ieee9500/Network.json')
#  i2x.parse_opendss_graph(G)
  G = i2x.load_builtin_graph('ieee9500')
#  G = i2x.load_builtin_graph('ieee_lvn')
  if G is not None:
    i2x.plot_opendss_feeder(G, plot_labels=True, legend_loc='upper right')
    i2x.parse_opendss_graph(G)
#  i2x.show_der_config()

