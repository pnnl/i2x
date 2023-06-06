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
#  G = i2x.load_builtin_graph('ieee9500')
#  G = i2x.load_builtin_graph('ieee_lvn')
#  if G is not None:
#    i2x.plot_opendss_feeder(G, plot_labels=True, legend_loc='upper right')
#    i2x.parse_opendss_graph(G)
#  i2x.show_der_config()

#  i2x.make_opendss_graph(saved_path='c:/ieee/p1729/HostingCapacityTF/TestFeeder/graph/',
#                         outfile='c:/ieee/p1729/HostingCapacityTF/TestFeeder/Network.json')
  G = i2x.load_opendss_graph('c:/ieee/p1729/HostingCapacityTF/TestFeeder/Network.json')
  if G is not None:
    i2x.plot_opendss_feeder(G, plot_labels=True, legend_loc='upper right')
    d = i2x.parse_opendss_graph(G, bSummarize=False)
    print ('Load = {:.2f} kW'.format(d['loadkw']))
    print ('Large DER')
    for key, row in d['largeder'].items():
      print ('  ', key, row)

