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
import py_dss_interface

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
import matplotlib
import pkg_resources
import datetime

try:
  matplotlib.use('TkAgg')
except:
  pass
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.pyplot as plt

import numpy as np

support_dir = 'models/support/'

# TODO: factor these into a separate file
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
             'p':[0.677,0.6256,0.6087,0.5833,0.58028,0.6025,0.657,0.7477,0.832,0.88,0.94,0.989,0.985,0.98,0.9898,0.999,1,0.958,0.936,0.913,0.876,0.876,0.828,0.756,0.677]},
  'flat':{'t':[0,24],'p':[1.0, 1.0]}
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

solutionModeChoices = ['SNAPSHOT', 'DAILY', 'DUTY', 'YEARLY']
controlModeChoices = ['OFF', 'STATIC', 'TIME', 'EVENT']

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

    self.f2 = ttk.Frame(self.nb, name='varsDER')
    self.UpdateFeeder(None) # this updates f2 with DER information on the selected feeder

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
    lab = ttk.Label(self.f4, text='Load Multiplier: ', relief=tk.RIDGE)
    lab.grid(row=0, column=2, sticky=tk.NSEW)
    self.ent_load_mult = ttk.Entry(self.f4, name='load_mult')
    self.ent_load_mult.insert(0, '1.0')
    self.ent_load_mult.grid(row=0, column=3, sticky=tk.NSEW)
    self.f4.columnconfigure(0, weight=0)
    self.f4.columnconfigure(1, weight=0)
    self.f4.columnconfigure(2, weight=0)
    self.f4.columnconfigure(3, weight=1)
    self.f4.rowconfigure(0, weight=0)
    self.f4.rowconfigure(1, weight=1)
    self.fig_load = plt.figure(figsize=(5, 4), dpi=100)
    self.ax_load = self.fig_load.add_subplot()
    self.ax_load.set_xlabel('Time [hr]')
    self.ax_load.set_ylabel('Power [pu]')
    self.canvas_load = FigureCanvasTkAgg(self.fig_load, master=self.f4)
    self.canvas_load.get_tk_widget().grid(row=1, columnspan=4, sticky=tk.W + tk.E + tk.N + tk.S)
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
    lab = ttk.Label(self.f6, text='Solution Mode', relief=tk.RIDGE)
    lab.grid(row=0, column=0, sticky=tk.NSEW)
    self.cb_soln_mode = ttk.Combobox(self.f6, values=solutionModeChoices, name='cbSolutionMode')
    self.cb_soln_mode.grid(row=0, column=1, sticky=tk.NSEW)
    self.cb_soln_mode.set('DAILY')
    lab = ttk.Label(self.f6, text='Control Mode', relief=tk.RIDGE)
    lab.grid(row=0, column=2, sticky=tk.NSEW)
    self.cb_ctrl_mode = ttk.Combobox(self.f6, values=controlModeChoices, name='cbControlMode')
    self.cb_ctrl_mode.grid(row=0, column=3, sticky=tk.NSEW)
    self.cb_ctrl_mode.set('STATIC')
    lab = ttk.Label(self.f6, text='Stop Time [min]:', relief=tk.RIDGE)
    lab.grid(row=1, column=0, sticky=tk.NSEW)
    self.ent_stop = ttk.Entry(self.f6, name='stop')
    self.ent_stop.insert(0, '1440')
    self.ent_stop.grid(row=1, column=1, sticky=tk.NSEW)
    lab = ttk.Label(self.f6, text='Time Step [s]:', relief=tk.RIDGE)
    lab.grid(row=1, column=2, sticky=tk.NSEW)
    self.ent_step = ttk.Entry(self.f6, name='step')
    self.ent_step.insert(0, '300')
    self.ent_step.grid(row=1, column=3, sticky=tk.NSEW)
    #ttk.Style().configure('TButton', background='blue')
    self.output_details = tk.IntVar()
    self.output_details.set(1)
    self.cbk_detail = ttk.Checkbutton(self.f6, text='Output PV Details', variable=self.output_details)
    self.cbk_detail.grid(row=2, column=0, sticky=tk.NSEW)
    ttk.Style().configure('TButton', foreground='blue')
    self.btn_run = ttk.Button(self.f6, text='Run', command=self.RunOpenDSS)
    self.btn_run.grid(row=2, column=1, sticky=tk.NSEW)
    self.txt_output = scrolledtext.ScrolledText(self.f6)
    self.txt_output.grid(row=3, columnspan=4, sticky=tk.W + tk.E + tk.N + tk.S)
    self.f6.rowconfigure (0, weight=0)
    self.f6.rowconfigure (1, weight=0)
    self.f6.rowconfigure (2, weight=0)
    self.f6.rowconfigure (3, weight=1)
    self.f6.columnconfigure (0, weight=0)
    self.f6.columnconfigure (1, weight=0)
    self.f6.columnconfigure (2, weight=0)
    self.f6.columnconfigure (3, weight=1)

    self.nb.add(self.f1, text='Network', underline=0, padding=2)
    self.nb.add(self.f2, text='DER', underline=0, padding=2)
    self.nb.add(self.f3, text='Solar', underline=0, padding=2)
    self.nb.add(self.f4, text='Loads', underline=0, padding=2)
    self.nb.add(self.f5, text='Inverters', underline=0, padding=2)
    self.nb.add(self.f6, text='Output', underline=0, padding=2)

  def on_closing(self):
    self.master.quit()
    self.master.destroy()
#    if messagebox.askokcancel('Quit', 'Do you want to close this window? This is likely to stop all simulations.'):
#      self.master.quit()
#      self.master.destroy()

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
  def RunOpenDSS(self):
    load_mult = float(self.ent_load_mult.get())
    feeder_choice = self.cb_feeder.get()
    soln_mode = self.cb_soln_mode.get()
    ctrl_mode = self.cb_ctrl_mode.get()
    solar_profile = self.cb_solar.get()
    load_profile = self.cb_load.get()
    inv_mode = self.cb_inverter.get()
    stop_minutes = int(self.ent_stop.get())
    step_seconds = int(self.ent_step.get())
    num_steps = int (60 * stop_minutes / step_seconds)
    print (feeder_choice, solar_profile, load_mult, load_profile, inv_mode,
           soln_mode, ctrl_mode, step_seconds, num_steps)
    dict = i2x.test_opendss_interface(choice = feeder_choice,
                                      pvcurve = solar_profile,
                                      loadmult = load_mult,
                                      loadcurve = load_profile,
                                      invmode = inv_mode, 
                                      stepsize = step_seconds, 
                                      numsteps = num_steps,
                                      ctrlmode = ctrl_mode,
                                      solnmode = soln_mode, 
                                      doc_fp=None)
    self.txt_output.insert(tk.END, 'Analysis Run on {:s} at {:s}'.format(feeder_choice, datetime.datetime.now().strftime('%a %d-%b-%Y %H:%M:%S')))
    self.txt_output.insert(tk.END, 'Number of Capacitor Switchings = {:d}\n'.format(dict['num_cap_switches']))
    self.txt_output.insert(tk.END, 'Number of Tap Changes = {:d}\n'.format(dict['num_tap_changes']))
    self.txt_output.insert(tk.END, 'Number of Relay Trips = {:d}\n'.format(dict['num_relay_trips']))
    self.txt_output.insert(tk.END, '{:d} Nodes with Low Voltage, Lowest={:.4f}pu at {:s}\n'.format(dict['num_low_voltage'], dict['vminpu'], dict['node_vmin']))
    self.txt_output.insert(tk.END, '{:d} Nodes with High Voltage, Highest={:.4f}pu at {:s}\n'.format(dict['num_high_voltage'], dict['vmaxpu'], dict['node_vmax']))
    self.txt_output.insert(tk.END, 'Substation Energy =         {:11.2f} kWh\n'.format(dict['kWh_Net']))
    self.txt_output.insert(tk.END, 'Load Served =               {:11.2f} kWh\n'.format(dict['kWh_Load']))
    self.txt_output.insert(tk.END, 'Losses =                    {:11.2f} kWh\n'.format(dict['kWh_Loss']))
    self.txt_output.insert(tk.END, 'Generation =                {:11.2f} kWh\n'.format(dict['kWh_Gen']))
    self.txt_output.insert(tk.END, 'Solar Output =              {:11.2f} kWh\n'.format(dict['kWh_PV']))
    self.txt_output.insert(tk.END, 'Solar Reactive Power =      {:11.2f} kWh\n'.format(dict['kvarh_PV']))
    self.txt_output.insert(tk.END, 'Energy Exceeding Normal =   {:11.2f} kWh\n'.format(dict['kWh_EEN']))
    self.txt_output.insert(tk.END, 'Unserved Energy =           {:11.2f} kWh\n'.format(dict['kWh_UE']))
    self.txt_output.insert(tk.END, 'Normal Overload Energy =    {:11.2f} kWh\n'.format(dict['kWh_OverN']))
    self.txt_output.insert(tk.END, 'Emergency Overload Energy = {:11.2f} kWh\n'.format(dict['kWh_OverE']))

    if self.output_details.get() > 0:
      self.txt_output.insert(tk.END, 'PV Name                    kWh     kvarh     Vmin     Vmax    Vmean    Vdiff\n')
      for key, row in dict['pvdict'].items():
        self.txt_output.insert(tk.END, '{:20s} {:9.2f} {:9.2f} {:8.2f} {:8.2f} {:8.2f} {:8.2f}\n'.format(key, row['kWh'], row['kvarh'], 
                                                                               row['vmin'], row['vmax'], row['vmean'], row['vdiff']))


  def ResetDERPage(self):
    for w in self.f2.grid_slaves():
      w.grid_forget()

    pvkw = 0.0
    pvkva = 0.0
    npv = len(self.pvder)
    for key, row in self.pvder.items():
      pvkw += row['kw']
      pvkva += row['kva']

    genkw = 0.0
    genkva = 0.0
    ngen = len(self.gender)
    for key, row in self.gender.items():
      genkw += row['kw']
      genkva += row['kva']

    batkw = 0.0
    batkva = 0.0
    nbat = len(self.batder)
    for key, row in self.batder.items():
      batkw += row['kw']
      batkva += row['kva']

    lab_load = ttk.Label(self.f2, text='Total Load = {:.2f} kW'.format(self.loadkw), relief=tk.RIDGE)
    lab_load.grid(row=0, column=0, sticky=tk.NSEW)
    lab_pv = ttk.Label(self.f2, text='Existing Solar = {:.2f} kVA, {:.2f} kW in {:d} units'.format(pvkva, pvkw, npv), relief=tk.RIDGE)
    lab_pv.grid(row=1, column=0, sticky=tk.NSEW)
    lab_bat = ttk.Label(self.f2, text='Existing Storage = {:.2f} kVA, {:.2f} kW in {:d} units'.format(batkva, batkw, nbat), relief=tk.RIDGE)
    lab_bat.grid(row=2, column=0, sticky=tk.NSEW)
    lab_gen = ttk.Label(self.f2, text='Existing Generation = {:.2f} kVA, {:.2f} kW in {:d} units'.format(genkva, genkw, ngen), relief=tk.RIDGE)
    lab_gen.grid(row=3, column=0, sticky=tk.NSEW)
    lab_roofs = ttk.Label(self.f2, text='{:d} Available Residential Rooftops, Use[%]:'.format(len(self.resloads)), relief=tk.RIDGE)
    lab_roofs.grid(row=4, column=0, sticky=tk.NSEW)
    self.ent_pct_roofs = ttk.Entry(self.f2, name='pct_roofs')
    self.ent_pct_roofs.insert(0, '10.0')
    self.ent_pct_roofs.grid(row=4, column=1, sticky=tk.NSEW)

    lab = ttk.Label(self.f2, text='DER >= 100.0 kVA')
    lab.grid(row=5, column=0, sticky=tk.NSEW)
    lab = ttk.Label(self.f2, text='kW')
    lab.grid(row=5, column=1, sticky=tk.NSEW)
    lab = ttk.Label(self.f2, text='kVA')
    lab.grid(row=5, column=2, sticky=tk.NSEW)
    lab = ttk.Label(self.f2, text='Type')
    lab.grid(row=5, column=3, sticky=tk.NSEW)

    idx = 6
    for key, row in self.largeder.items():
      lab = ttk.Label(self.f2, text='Name={:s} Bus={:s} kV={:.2f} kW={:.2f} kVA={:.2f} Type={:s}'.format (key,
                                                                                                          row['bus'],
                                                                                                          row['kv'],
                                                                                                          row['kw'],
                                                                                                          row['kva'],
                                                                                                          row['type']), 
                      relief=tk.RIDGE)
      lab.grid(row=idx, column=0, sticky=tk.NSEW)
      e1 = ttk.Entry(self.f2, name='kw_{:s}'.format(key))
      e1.insert(0, str(row['kw']))
      e1.grid(row=idx, column=1, sticky=tk.NSEW)
      e2 = ttk.Entry(self.f2, name='kva_{:s}'.format(key))
      e2.insert(0, str(row['kva']))
      e2.grid(row=idx, column=2, sticky=tk.NSEW)
      cb1 = ttk.Combobox(self.f2, values=['solar','storage','generator'], name='type_{:s}'.format(key))
      cb1.set(row['type'])
      cb1.grid(row=idx, column=3, sticky=tk.NSEW)
      idx += 1

  def UpdateFeeder(self, event):
    key = self.cb_feeder.get()
    row = feederChoices[key]
    self.feeder_name = key
    self.feeder_path = row['path']
    self.feeder_base = row['base']
    fname = pkg_resources.resource_filename (__name__, row['path'] + row['network'])
    self.G = i2x.load_opendss_graph(fname)

    self.pvder, self.gender, self.batder, self.largeder, self.resloads, self.loadkw = i2x.parse_opendss_graph(self.G)

    self.ax_feeder.cla()
    i2x.plot_opendss_feeder (self.G, plot_labels=True, on_canvas=True, 
                             ax=self.ax_feeder, fig=self.fig_feeder)
    self.canvas_feeder.draw()
    self.ResetDERPage()

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
# def SaveConfig(self):
#   fname = filedialog.asksaveasfilename(initialdir='~/src/examples/te30',
#                      title='Save JSON Configuration to',
#                      defaultextension='json')
#   if len(fname) > 0:
#     op = open(fname, 'w')
#     json.dump(config, op, ensure_ascii=False, indent=2)
#     op.close()
#
# def OpenConfig(self):
#   fname = filedialog.askopenfilename(initialdir='~/src/examples/te30',
#                      title='Open JSON Configuration',
#                      filetypes=(("JSON files", "*.json"), ("all files", "*.*")),
#                      defaultextension='json')
#   lp = open(fname)
#   cfg = json.loads(lp.read())
#   lp.close()
#

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
