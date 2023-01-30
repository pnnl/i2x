# Copyright (C) 2023 Battelle Memorial Institute
# file: der.py
"""Presents a GUI for DER boot camp

Public Functions:
#  :show_der_config: Initializes and runs the GUI

"""
import i2x.api as i2x

if __name__ == "__main__":
#  i2x.make_opendss_graph('./ieee9500/graph/', './ieee9500/Network.json')
#  i2x.make_opendss_graph('./ieee_lvn/graph/', './ieee_lvn/Network.json')
#  i2x.plot_opendss_feeder('./ieee9500/Network.json', plot_labels=False)
  i2x.plot_opendss_feeder('./ieee_lvn/Network.json')
#  i2x.show_der_config()
#  i2x.show_der_monitor()

