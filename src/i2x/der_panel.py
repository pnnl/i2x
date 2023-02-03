# Copyright (C) 2017-2023 Battelle Memorial Institute
# file: der_panel.py
"""Presents a GUI to configure and package DER simulation cases

Public Functions:
  :show_der_config: Initializes and runs the GUI

References:
  `Graphical User Interfaces with Tk <https://docs.python.org/3/library/tk.html>`_
"""
import csv
import json
import os
import i2x.api as i2x

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
import matplotlib
import pkg_resources

try:
  matplotlib.use('TkAgg')
except:
  pass
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.pyplot as plt

import numpy as np

support_dir = 'models/support/'

feederChoices = {
  'ieee9500':{'path':'models/ieee9500/', 'base':'Master-bal-initial-config.dss', 'network':'Network.json'},
  'ieee_lvn':{'path':'models/ieee_lvn/', 'base':'SecPar.dss', 'network':'Network.json'}
  }

solarChoices = {
  'pclear':{'dt':1.0, 'file':'pclear.dat', 'npts':0, 'data':None},
  'pcloud':{'dt':1.0, 'file':'pcloud.dat', 'npts':0, 'data':None},
  'pvduty':{'dt':1.0, 'file':'pvloadshape-1sec-2900pts.dat', 'npts':0, 'data':None}
  }

loadChoices = {
  'default':{'t':[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24],
             'p':[0.677,0.6256,0.6087,0.5833,0.58028,0.6025,0.657,0.7477,0.832,0.88,0.94,0.989,0.985,0.98,0.9898,0.999,1,0.958,0.936,0.913,0.876,0.876,0.828,0.756,0.677]}
  }

inverterChoices = {
  'CONSTANT_PF':{'v':[0.90,1.10],
                 'p':[1.00,1.00],
                 'q':[0.00,0.00]},
  'VOLT_WATT':{'v':[0.90,1.06,1.10],
               'p':[1.00,1.00,0.20],
               'q':[0.00,0.00,0.00]}, 
  'VOLT_VAR':{'v':[0.90,0.92,0.98,1.02,1.08,1.10],
              'p':[1.00,1.00,1.00,1.00,1.00,1.00],
              'q':[0.44,0.44,0.00,0.00,-.44,-.44]},
  'VOLT_VAR_AVR':{'v':[0.90,0.98,1.02,1.10],
                  'p':[1.00,1.00,1.00,1.00],
                  'q':[0.44,0.44,-.44,-.44]}, 
  'VOLT_VAR_VOLT_WATT':{'v':[0.90,0.92,0.98,1.02,1.06,1.10],
                        'p':[1.00,1.00,1.00,1.00,1.00,0.00],
                        'q':[0.44,0.44,0.00,0.00,-.44,-.44]}
  }

# var columns are label, value, hint, JSON class, JSON attribute
# if there is a sixth column, that will be the name of a Choices tuple, to be edited via Combobox
# if there is not a sixth column, that indicates a single value to be edited via Entry

class DERConfigGUI:
  """Manages a seven-page GUI for case configuration

  The GUI opens and saves a JSON file in the format used by *tesp.tesp_config*

  Todo:
    * Possible data loss if the user updated the number of Monte Carlo cases, but didn't click the Update button before saving the case configuration.

  Attributes:
    nb (Notebook): the top-level GUI with tabbed pages
    f1 (Frame): the page for feeder selection
    f2 (Frame): the page for DER placement
    f3 (Frame): the page for solar profile selection
    f4 (Frame): the page for load profile selection
    f5 (Frame): the page for inverter profile selection
    f6 (Frame): the page for time-scheduled thermostat settings
  """

  def __init__(self, master):
    self.master = master
    self.master.protocol('WM_DELETE_WINDOW', self.on_closing)

    self.nb = ttk.Notebook(master)
    self.nb.pack(fill='both', expand='yes')

    for key, row in solarChoices.items():
#      fname = os.path.join (support_dir, row['file'])
      fname = pkg_resources.resource_filename (__name__, support_dir + row['file'])
      row['data'] = np.loadtxt (fname)
      row['npts'] = row['data'].shape[0]
      peak = max(np.abs(row['data']))
      row['data'] /= peak

    self.f1 = ttk.Frame(self.nb, name='varsNet')
    lab = ttk.Label(self.f1, text='Feeder Model: ', relief=tk.RIDGE)
    lab.grid(row=0, column=0, sticky=tk.NSEW)
    self.cb_feeder = ttk.Combobox(self.f1, values=[i for i in feederChoices], name='cbFeeders')
    self.cb_feeder.set(next(iter(feederChoices)))
    self.cb_feeder.grid(row=0, column=1, sticky=tk.NSEW)
    self.cb_feeder.bind('<<ComboboxSelected>>', self.UpdateFeeder)
    self.f1.columnconfigure(0, weight=0)
    self.f1.columnconfigure(1, weight=1)
    self.f1.rowconfigure(0, weight=0)
    self.f1.rowconfigure(1, weight=1)

    self.fig_feeder = plt.figure(figsize=(5, 4), dpi=100)
    self.ax_feeder = self.fig_feeder.add_subplot()
    t = np.arange(0, 3, .01)
    line, = self.ax_feeder.plot(t, 2 * np.sin(2 * np.pi * t))
    self.ax_feeder.set_xlabel('time [s]')
    self.ax_feeder.set_ylabel('f(t)')

    self.canvas_feeder = FigureCanvasTkAgg(self.fig_feeder, master=self.f1)
    self.canvas_feeder.get_tk_widget().grid(row=1, columnspan=2, sticky=tk.W + tk.E + tk.N + tk.S)
    self.canvas_feeder.draw()
    self.toolbar = NavigationToolbar2Tk(self.canvas_feeder, self.f1, pack_toolbar=False)
    self.toolbar.update()
    self.toolbar.grid(row=2, columnspan=2)
    self.UpdateFeeder(None)

    self.f2 = ttk.Frame(self.nb, name='varsDER')

    self.f3 = ttk.Frame(self.nb, name='varsSolar')
    lab = ttk.Label(self.f3, text='Solar Profile: ', relief=tk.RIDGE)
    lab.grid(row=0, column=0, sticky=tk.NSEW)
    self.cb_solar = ttk.Combobox(self.f3, values=[i for i in solarChoices], name='cbSolars')
    self.cb_solar.set(next(iter(solarChoices)))
    self.cb_solar.grid(row=0, column=1, sticky=tk.NSEW)
    self.cb_solar.bind('<<ComboboxSelected>>', self.UpdateSolarProfile)
    self.f3.columnconfigure(0, weight=0)
    self.f3.columnconfigure(1, weight=1)
    self.f3.rowconfigure(0, weight=0)
    self.f3.rowconfigure(1, weight=1)
    self.fig_solar = plt.figure(figsize=(5, 4), dpi=100)
    self.ax_solar = self.fig_solar.add_subplot()
    self.ax_solar.set_xlabel('Time [hr]')
    self.ax_solar.set_ylabel('Power [pu]')
    self.canvas_solar = FigureCanvasTkAgg(self.fig_solar, master=self.f3)
    self.canvas_solar.get_tk_widget().grid(row=1, columnspan=2, sticky=tk.W + tk.E + tk.N + tk.S)
    self.canvas_solar.draw()
    self.UpdateSolarProfile(None)

    self.f4 = ttk.Frame(self.nb, name='varsLoad')
    lab = ttk.Label(self.f4, text='Load Profile: ', relief=tk.RIDGE)
    lab.grid(row=0, column=0, sticky=tk.NSEW)
    self.cb_load = ttk.Combobox(self.f4, values=[i for i in loadChoices], name='cbLoads')
    self.cb_load.set(next(iter(loadChoices)))
    self.cb_load.grid(row=0, column=1, sticky=tk.NSEW)
    self.cb_load.bind('<<ComboboxSelected>>', self.UpdateLoadProfile)
    self.f4.columnconfigure(0, weight=0)
    self.f4.columnconfigure(1, weight=1)
    self.f4.rowconfigure(0, weight=0)
    self.f4.rowconfigure(1, weight=1)
    self.fig_load = plt.figure(figsize=(5, 4), dpi=100)
    self.ax_load = self.fig_load.add_subplot()
    self.ax_load.set_xlabel('Time [hr]')
    self.ax_load.set_ylabel('Power [pu]')
    self.canvas_load = FigureCanvasTkAgg(self.fig_load, master=self.f4)
    self.canvas_load.get_tk_widget().grid(row=1, columnspan=2, sticky=tk.W + tk.E + tk.N + tk.S)
    self.canvas_load.draw()
    self.UpdateLoadProfile(None)

    self.f5 = ttk.Frame(self.nb, name='varsInverter')
    lab = ttk.Label(self.f5, text='Inverter Mode: ', relief=tk.RIDGE)
    lab.grid(row=0, column=0, sticky=tk.NSEW)
    self.cb_inverter = ttk.Combobox(self.f5, values=[i for i in inverterChoices], name='cbInverters')
    self.cb_inverter.set(next(iter(inverterChoices)))
    self.cb_inverter.grid(row=0, column=1, sticky=tk.NSEW)
    self.cb_inverter.bind('<<ComboboxSelected>>', self.UpdateInverterMode)
    self.f5.columnconfigure(0, weight=0)
    self.f5.columnconfigure(1, weight=1)
    self.f5.rowconfigure(0, weight=0)
    self.f5.rowconfigure(1, weight=1)
    self.fig_inverter = plt.figure(figsize=(5, 4), dpi=100)
    self.ax_inverter = self.fig_inverter.add_subplot()
    self.ax_inverter.set_xlabel('Voltage [pu]')
    self.ax_inverter.set_ylabel('Power [pu]')
    self.canvas_inverter = FigureCanvasTkAgg(self.fig_inverter, master=self.f5)
    self.canvas_inverter.get_tk_widget().grid(row=1, columnspan=2, sticky=tk.W + tk.E + tk.N + tk.S)
    self.canvas_inverter.draw()
    self.UpdateInverterMode(None)

    self.f6 = ttk.Frame(self.nb, name='varsOutput')
#

    # ttk.Style().configure('TButton', background='blue')
#   ttk.Style().configure('TButton', foreground='blue')
#   btn = ttk.Button(self.f1, text='Lat/Long/Alt/TZ from TMY3', command=self.ReadLatLong)
#   btn.grid(row=len(varsTM) + 2, column=1, sticky=tk.NSEW)
#   btn = ttk.Button(self.f1, text='Save Config...', command=self.SaveConfig)
#   btn.grid(row=len(varsTM) + 3, column=1, sticky=tk.NSEW)
#   btn = ttk.Button(self.f1, text='Open Config...', command=self.OpenConfig)
#   btn.grid(row=len(varsTM) + 4, column=1, sticky=tk.NSEW)
#
#   lab = ttk.Label(self.f7, text='Columns', relief=tk.RIDGE)
#   lab.grid(row=0, column=0, sticky=tk.NSEW)
#   cb = ttk.Combobox(self.f7, values=monteCarloChoices, name='cb1')
#   cb.set(monteCarloChoices[1])
#   cb.grid(row=0, column=1, sticky=tk.NSEW)
#   cb = ttk.Combobox(self.f7, values=monteCarloChoices, name='cb2')
#   cb.set(monteCarloChoices[2])
#   cb.grid(row=0, column=2, sticky=tk.NSEW)
#   cb = ttk.Combobox(self.f7, values=monteCarloChoices, name='cb3')
#   cb.set(monteCarloChoices[3])
#   cb.grid(row=0, column=3, sticky=tk.NSEW)
#
#   self.InitializeMonteCarlo(7)
#   lab = ttk.Label(self.f7, text='Rows', relief=tk.RIDGE)
#   lab.grid(row=1, column=0, sticky=tk.NSEW)
#   ent = ttk.Entry(self.f7, name='rows')
#   ent.insert(0, config['MonteCarloCase']['NumCases'])
#   ent.grid(row=1, column=1, sticky=tk.NSEW)
#   btn = ttk.Button(self.f7, text='Update', command=self.UpdateMonteCarloFrame)
#   btn.grid(row=1, column=3, sticky=tk.NSEW)
#   self.SizeMonteCarlo(config['MonteCarloCase']['NumCases'])
#   self.SizeMonteCarloFrame(self.f7)
#
    self.nb.add(self.f1, text='Network', underline=0, padding=2)
    self.nb.add(self.f2, text='DER', underline=0, padding=2)
    self.nb.add(self.f3, text='Solar', underline=0, padding=2)
    self.nb.add(self.f4, text='Loads', underline=0, padding=2)
    self.nb.add(self.f5, text='Inverters', underline=0, padding=2)
    self.nb.add(self.f6, text='Output', underline=0, padding=2)

  def on_closing(self):
    if messagebox.askokcancel('Quit', 'Do you want to close this window? This is likely to stop all simulations.'):
      self.master.quit()
      self.master.destroy()

# def AttachFrame(self, tag, vars):
#   """Creates a GUI page and loads it with data
#
#   Label, Combobox and Entry (i.e. edit) controls are automatically created for each row of data
#
#   Args:
#     tag (str): the name of the Frame, i.e., GUI page
#     vars (dict): the section of case configuration data to be loaded onto this new GUI page
#   """
#   f = ttk.Frame(self.nb, name=tag)
#   lab = ttk.Label(f, text='Parameter', relief=tk.RIDGE)
#   lab.grid(row=0, column=0, sticky=tk.NSEW)
#   lab = ttk.Label(f, text='Value', relief=tk.RIDGE)
#   lab.grid(row=0, column=1, sticky=tk.NSEW)
#   lab = ttk.Label(f, text='Units/Notes', relief=tk.RIDGE)
#   lab.grid(row=0, column=2, sticky=tk.NSEW)
#   for i in range(len(vars)):
#     lab = ttk.Label(f, text=vars[i][0], relief=tk.RIDGE)
#     lab.grid(row=i + 1, column=0, sticky=tk.NSEW)
#     varName = (vars[i][3] + '#' + vars[i][4]).lower()
#     if len(vars[i]) > 5:
#       cb = ttk.Combobox(f, values=globals()[vars[i][5]], name=varName)
#       cb.set(vars[i][1])
#       cb.grid(row=i + 1, column=1, sticky=tk.NSEW)
#     else:
#       ent = ttk.Entry(f, name=varName)
#       ent.insert(0, vars[i][1])
#       ent.grid(row=i + 1, column=1, sticky=tk.NSEW)
#     lab = ttk.Label(f, text=vars[i][2], relief=tk.RIDGE)
#     lab.grid(row=i + 1, column=2, sticky=tk.NSEW)
#   f.columnconfigure(0, weight=1)
#   f.columnconfigure(1, weight=2)
#   f.columnconfigure(2, weight=1)
#   return f
#
# def ReloadFrame(self, f, vars):
#   """Helper function to recreate the GUI page controls and load them with values
#
#   Args:
#     f (Frame): the GUI page to reload
#     vars (dict): the section of case configuration with values to be loaded
#   """
#   for i in range(len(vars)):
#     ent = f.grid_slaves(row=i + 1, column=1)[0]
#     ent.delete(0, tk.END)
#     ent.insert(0, vars[i][1])
#
# def mcSample(self, var):
#   """Return an appropriate random value for each Monte Carlo variable choice
#
#   Args:
#     var (str): one of ElectricCoolingParticipation, ThermostatRampMid, ThermostatOffsetLimitMid, WeekdayEveningStartMid or WeekdayEveningSetMid
#   """
#   if var == 'ElectricCoolingParticipation':
#     return '{:.3f}'.format(np.random.uniform(0, 100))
#   elif var == 'ThermostatRampMid':
#     return '{:.3f}'.format(np.random.uniform(1.0, 4.0))
#   elif var == 'ThermostatOffsetLimitMid':
#     return '{:.3f}'.format(np.random.uniform(0, 6.0))
#   elif var == 'WeekdayEveningStartMid':
#     return '{:.3f}'.format(np.random.uniform(16.5, 18.0))
#   elif var == 'WeekdayEveningSetMid':
#     return '{:.3f}'.format(np.random.uniform(68.0, 74.0))
#   else:
#     return '{:.3f}'.format(np.random.uniform(0, 1))
#
# def mcBand(self, var):
#   """Find the band size corresponding to each Monte Carlo variable choice
#
#   Args:
#     var (str): one of ElectricCoolingParticipation, ThermostatRampMid, ThermostatOffsetLimitMid, WeekdayEveningStartMid or WeekdayEveningSetMid
#   """
#   if var == 'ElectricCoolingParticipation':
#     return 10.0
#   elif var == 'ThermostatRampMid':
#     return 0.5
#   elif var == 'ThermostatOffsetLimitMid':
#     return 2.0
#   elif var == 'WeekdayEveningStartMid':
#     return 1.0
#   elif var == 'WeekdayEveningSetMid':
#     return 1.0
#   else:
#     return 0.0
#
# def SizeMonteCarlo(self, n):
#   """Initializes the Monte Carlo data structures with variable choices and samples
#
#   Args:
#     n (int): the number of Monte Carlo shots
#   """
#   var1 = config['MonteCarloCase']['Variable1']
#   var2 = config['MonteCarloCase']['Variable2']
#   var3 = config['MonteCarloCase']['Variable3']
#   config['MonteCarloCase']['NumCases'] = n
#   config['MonteCarloCase']['Band1'] = self.mcBand(var1)
#   config['MonteCarloCase']['Band2'] = self.mcBand(var2)
#   config['MonteCarloCase']['Band3'] = self.mcBand(var3)
#   config['MonteCarloCase']['Samples1'] = [0] * n
#   config['MonteCarloCase']['Samples2'] = [0] * n
#   config['MonteCarloCase']['Samples3'] = [0] * n
#   for i in range(n):
#     config['MonteCarloCase']['Samples1'][i] = self.mcSample(var1)
#     config['MonteCarloCase']['Samples2'][i] = self.mcSample(var2)
#     config['MonteCarloCase']['Samples3'][i] = self.mcSample(var3)
#
# def InitializeMonteCarlo(self, n):
#   """Makes default variable choices and then initializes the Monte Carlo GUI page
#
#   Args:
#     n (int): the number of Monte Carlo shots
#   """
#   config['MonteCarloCase']['Variable1'] = monteCarloChoices[1]
#   config['MonteCarloCase']['Variable2'] = monteCarloChoices[2]
#   config['MonteCarloCase']['Variable3'] = monteCarloChoices[3]
#   self.SizeMonteCarlo(n)
#
# # row 0 for dropdowns, 1 for update controls, 2 for column headers, 3 for range edits
# def SizeMonteCarloFrame(self, f):
#   """Update the Monte Carlo page to match the number of shots and variables
#
#   Args:
#     f (Frame): the Monte Carlo GUI page
#   """
#   startRow = 3
#   for w in f.grid_slaves():
#     if int(w.grid_info()['row']) > 2:
#       w.grid_forget()
#
#   col1 = f.children['cb1'].get()
#   col2 = f.children['cb2'].get()
#   col3 = f.children['cb3'].get()
#   use1 = col1 != 'None'
#   use2 = col2 != 'None'
#   use3 = col3 != 'None'
#   band1 = 'Mid' in col1
#   band2 = 'Mid' in col2
#   band3 = 'Mid' in col3
#
#   lab = ttk.Label(f, text='Case #', relief=tk.RIDGE)
#   lab.grid(row=startRow + 1, column=0, sticky=tk.NSEW)
#   lab = ttk.Label(f, text=col1, relief=tk.RIDGE)
#   lab.grid(row=startRow - 1, column=1, sticky=tk.NSEW)
#   lab = ttk.Label(f, text=col2, relief=tk.RIDGE)
#   lab.grid(row=startRow - 1, column=2, sticky=tk.NSEW)
#   lab = ttk.Label(f, text=col3, relief=tk.RIDGE)
#   lab.grid(row=startRow - 1, column=3, sticky=tk.NSEW)
#
#   lab = ttk.Label(f, text='Band', relief=tk.RIDGE)
#   lab.grid(row=startRow, column=0, sticky=tk.NSEW)
#   if band1:
#     w1 = ttk.Entry(f)
#     w1.insert(0, config['MonteCarloCase']['Band1'])
#   else:
#     w1 = ttk.Label(f, text='n/a', relief=tk.RIDGE)
#   if band2:
#     w2 = ttk.Entry(f)
#     w2.insert(0, config['MonteCarloCase']['Band2'])
#   else:
#     w2 = ttk.Label(f, text='n/a', relief=tk.RIDGE)
#   if band3:
#     w3 = ttk.Entry(f)
#     w3.insert(0, config['MonteCarloCase']['Band3'])
#   else:
#     w3 = ttk.Label(f, text='n/a', relief=tk.RIDGE)
#   w1.grid(row=startRow, column=1, sticky=tk.NSEW)
#   w2.grid(row=startRow, column=2, sticky=tk.NSEW)
#   w3.grid(row=startRow, column=3, sticky=tk.NSEW)
#
#   n = int(config['MonteCarloCase']['NumCases'])
#   for i in range(n):
#     lab = ttk.Label(f, text=str(i + 1), relief=tk.RIDGE)
#     lab.grid(row=i + 2 + startRow, column=0, sticky=tk.NSEW)
#     if use1:
#       w1 = ttk.Entry(f)
#       w1.insert(0, config['MonteCarloCase']['Samples1'][i])
#     else:
#       w1 = ttk.Label(f, text='n/a', relief=tk.RIDGE)
#     if use2:
#       w2 = ttk.Entry(f)
#       w2.insert(0, config['MonteCarloCase']['Samples2'][i])
#     else:
#       w2 = ttk.Label(f, text='n/a', relief=tk.RIDGE)
#     if use3:
#       w3 = ttk.Entry(f)
#       w3.insert(0, config['MonteCarloCase']['Samples3'][i])
#     else:
#       w3 = ttk.Label(f, text='n/a', relief=tk.RIDGE)
#     w1.grid(row=i + 2 + startRow, column=1, sticky=tk.NSEW)
#     w2.grid(row=i + 2 + startRow, column=2, sticky=tk.NSEW)
#     w3.grid(row=i + 2 + startRow, column=3, sticky=tk.NSEW)
#
# def ReadFrame(self, f, vars):
#   """Helper function that reads values from gridded GUI controls into the local case configuration
#
#   Args:
#     f (Frame): the GUI page to read
#     vars (dict): the local data structure to update
#   """
#   for w in f.grid_slaves():
#     col = int(w.grid_info()['column'])
#     row = int(w.grid_info()['row'])
#     if col == 1 and row > 0 and row <= len(vars):
#       val = w.get()
#       try:
#         tmp = int(val)
#         val = tmp
#       except:
#         try:
#           tmp = float(val)
#           val = tmp
#         except:
#           pass
#       section = vars[row - 1][3]
#       attribute = vars[row - 1][4]
#       config[section][attribute] = val
#
  def UpdateFeeder(self, event):
    key = self.cb_feeder.get()
    row = feederChoices[key]
    self.feeder_name = key
    self.feeder_path = row['path']
    self.feeder_base = row['base']
#    fname = os.path.join (self.feeder_path, row['network'])
    fname = pkg_resources.resource_filename (__name__, row['path'] + row['network'])
    self.G = i2x.load_opendss_graph(fname)

    self.ax_feeder.cla()
    i2x.plot_opendss_feeder (self.G, on_canvas=True, ax=self.ax_feeder, fig=self.fig_feeder)
    self.canvas_feeder.draw()

#    messagebox.showinfo(title='Combobox', message='Feeder File=' + fname)

  def UpdateSolarProfile(self, event):
    key = self.cb_solar.get()
    row = solarChoices[key]
    dt = row['dt']
    npts = row['npts']
    tmax = dt * (npts - 1)
    y = row['data']
    t = np.linspace (0.0, tmax, npts) / 3600.0
    self.ax_solar.cla()
    self.ax_solar.plot(t, y, color='blue')
    self.ax_solar.set_xlabel('Time [hr]')
    self.ax_solar.set_ylabel('Power [pu]')
    self.ax_solar.grid()
    self.canvas_solar.draw()

#    msg = 'Solar={:s} dt={:.1f}s tmax={:.1f}s npts={:d}'.format(key, dt, tmax, npts)
#    messagebox.showinfo(title='Combobox', message=msg)

  def UpdateLoadProfile(self, event):
    ticks = [0, 4, 8, 12, 16, 20, 24]
    key = self.cb_load.get()
    row = loadChoices[key]
    self.ax_load.cla()
    self.ax_load.plot(row['t'], row['p'], color='blue')
    self.ax_load.set_xlabel('Hour [pu]')
    self.ax_load.set_ylabel('Power [pu]')
    self.ax_load.set_xticks(ticks)
    self.ax_load.set_xlim(ticks[0], ticks[-1])
    self.ax_load.grid()
    self.canvas_load.draw()

  def UpdateInverterMode(self, event):
    ticks = [0.90, 0.92, 0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.08, 1.10]
    key = self.cb_inverter.get()
    row = inverterChoices[key]
    self.ax_inverter.cla()
    self.ax_inverter.plot(row['v'], row['p'], label='Real', color='blue')
    self.ax_inverter.plot(row['v'], row['q'], label='Reactive', color='red')
    self.ax_inverter.set_xlabel('Voltage [pu]')
    self.ax_inverter.set_ylabel('Power [pu]')
    self.ax_inverter.set_xticks(ticks)
    self.ax_inverter.set_xlim(ticks[0], ticks[-1])
    self.ax_inverter.grid()
    self.ax_inverter.legend()
    self.canvas_inverter.draw()
#
# def update_entry(self, ctl, val):
#   ctl.delete(0, tk.END)
#   ctl.insert(0, val)
#
# def ReadLatLong(self):
#   """Updates the Latitude and Longitude from TMY3 file
#   """
#   weatherpath = self.path_ent.get()
#   weatherfile = self.tmy3_ent.get()
#   fname = weather_path + weatherfile
#   if os.path.isfile(fname):
#     fd = open(fname, 'r')
#     rd = csv.reader(fd, delimiter=',', skipinitialspace=True)
#     row = next(rd)
#     tmy3source = row[0]
#     tmy3station = row[1]
#     tmy3state = row[2]
#     tmy3tzoffset = float(row[3])
#     tmy3latitude = float(row[4])
#     tmy3longitude = float(row[5])
#     tmy3altitude = float(row[6])
#     self.update_entry(self.tz_ent, tmy3tzoffset)
#     self.update_entry(self.lat_ent, tmy3latitude)
#     self.update_entry(self.long_ent, tmy3longitude)
#     self.update_entry(self.alt_ent, tmy3altitude)
#     fd.close()
#   else:
#     print(fname, 'not found')
#
# def SaveConfig(self):
#   """Updates the local case configuration from the GUI, queries user for a file name, and then saves case configuration to that file
#   """
#   self.ReadFrame(self.f1, varsTM)
#   self.ReadFrame(self.f2, varsFD)
#   self.ReadFrame(self.f3, varsPP)
#   self.ReadFrame(self.f4, varsEP)
#   self.ReadFrame(self.f5, varsAC)
#   self.ReadFrame(self.f6, varsTS)
#
#   col1 = self.f7.children['cb1'].get()
#   col2 = self.f7.children['cb2'].get()
#   col3 = self.f7.children['cb3'].get()
#   config['MonteCarloCase']['Variable1'] = col1
#   config['MonteCarloCase']['Variable2'] = col2
#   config['MonteCarloCase']['Variable3'] = col3
#   use1 = col1 != 'None'
#   use2 = col2 != 'None'
#   use3 = col3 != 'None'
#   band1 = 'Mid' in col1
#   band2 = 'Mid' in col2
#   band3 = 'Mid' in col3
#   numCases = int(
#     self.f7.children['rows'].get())  # what if user changed entry and didn't click Update...global numCases?
#   for w in self.f7.grid_slaves():
#     row = int(w.grid_info()['row'])
#     col = int(w.grid_info()['column'])
#     if row == 3:
#       if col == 1 and band1:
#         val = float(w.get())
#         config['MonteCarloCase']['Band1'] = val
#       if col == 2 and band2:
#         val = float(w.get())
#         config['MonteCarloCase']['Band2'] = val
#       if col == 3 and band3:
#         val = float(w.get())
#         config['MonteCarloCase']['Band3'] = val
#     elif row > 4:
#       if col == 1 and use1:
#         val = float(w.get())
#         config['MonteCarloCase']['Samples1'][row - 5] = val
#       if col == 2 and use2:
#         val = float(w.get())
#         config['MonteCarloCase']['Samples2'][row - 5] = val
#       if col == 3 and use3:
#         val = float(w.get())
#         config['MonteCarloCase']['Samples3'][row - 5] = val
#   if not os.path.exists(tesp_share):
#     if not messagebox.askyesno('Continue to Save?', 'TESP Support Directory: ' + tesp_share + ' not found.'):
#       return
#   fname = filedialog.asksaveasfilename(initialdir='~/src/examples/te30',
#                      title='Save JSON Configuration to',
#                      defaultextension='json')
#   if len(fname) > 0:
#     op = open(fname, 'w')
#     json.dump(config, op, ensure_ascii=False, indent=2)
#     op.close()
#
# def JsonToSection(self, jsn, vars):
#   """Helper function that transfers a JSON file segment into GUI data structures
#
#   Args:
#     jsn (dict): the loaded JSON file
#     vars (dict): the local data structure
#   """
#   for i in range(len(vars)):
#     section = vars[i][3]
#     attribute = vars[i][4]
#     vars[i][1] = jsn[section][attribute]
#     config[section][attribute] = jsn[section][attribute]
#
# def OpenConfig(self):
#   """Opens a JSON case configuration; transfers its data to the GUI
#   """
#   fname = filedialog.askopenfilename(initialdir='~/src/examples/te30',
#                      title='Open JSON Configuration',
#                      filetypes=(("JSON files", "*.json"), ("all files", "*.*")),
#                      defaultextension='json')
#   lp = open(fname)
#   cfg = json.loads(lp.read())
#   lp.close()
#   self.JsonToSection(cfg, varsTM)
#   self.JsonToSection(cfg, varsFD)
#   self.JsonToSection(cfg, varsPP)
#   self.JsonToSection(cfg, varsEP)
#   self.JsonToSection(cfg, varsAC)
#   self.JsonToSection(cfg, varsTS)
#   self.ReloadFrame(self.f1, varsTM)
#   self.ReloadFrame(self.f2, varsFD)
#   self.ReloadFrame(self.f3, varsPP)
#   self.ReloadFrame(self.f4, varsEP)
#   self.ReloadFrame(self.f5, varsAC)
#   self.ReloadFrame(self.f6, varsTS)
#
#   numCases = int(cfg['MonteCarloCase']['NumCases'])
#   config['MonteCarloCase']['NumCases'] = numCases
#   ent = self.f7.children['rows']
#   ent.delete(0, tk.END)
#   ent.insert(0, str(numCases))
#
#   var1 = cfg['MonteCarloCase']['Variable1']
#   config['MonteCarloCase']['Variable1'] = var1
#   self.f7.children['cb1'].set(var1)
#
#   var2 = cfg['MonteCarloCase']['Variable2']
#   config['MonteCarloCase']['Variable2'] = var2
#   self.f7.children['cb2'].set(var2)
#
#   var3 = cfg['MonteCarloCase']['Variable3']
#   config['MonteCarloCase']['Variable3'] = var3
#   self.f7.children['cb3'].set(var3)
#
#   config['MonteCarloCase']['Band1'] = cfg['MonteCarloCase']['Band1']
#   config['MonteCarloCase']['Band2'] = cfg['MonteCarloCase']['Band2']
#   config['MonteCarloCase']['Band3'] = cfg['MonteCarloCase']['Band3']
#
#   config['MonteCarloCase']['Samples1'] = [0] * numCases
#   config['MonteCarloCase']['Samples2'] = [0] * numCases
#   config['MonteCarloCase']['Samples3'] = [0] * numCases
#
#   for i in range(numCases):
#     config['MonteCarloCase']['Samples1'][i] = cfg['MonteCarloCase']['Samples1'][i]
#     config['MonteCarloCase']['Samples2'][i] = cfg['MonteCarloCase']['Samples2'][i]
#     config['MonteCarloCase']['Samples3'][i] = cfg['MonteCarloCase']['Samples3'][i]
#
#   self.SizeMonteCarloFrame(self.f7)
#
# def UpdateMonteCarloFrame(self):
#   """Transfer data from the Monte Carlo page into the case configuration
#   """
#   numCases = int(self.f7.children['rows'].get())
#   config['MonteCarloCase']['Variable1'] = self.f7.children['cb1'].get()
#   config['MonteCarloCase']['Variable2'] = self.f7.children['cb2'].get()
#   config['MonteCarloCase']['Variable3'] = self.f7.children['cb3'].get()
#   self.SizeMonteCarlo(numCases)
#   self.SizeMonteCarloFrame(self.f7)

def show_der_config():
  """Runs the GUI. Reads and writes JSON case configuration files.
  """
  root = tk.Tk()
  root.title('i2x Test Systems: DER Cases')
  my_gui = DERConfigGUI(root)
  while True:
    try:
      root.mainloop()
      break
    except UnicodeDecodeError:
      pass


if __name__ == "__main__":
  show_der_config()
