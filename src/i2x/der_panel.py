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
from tkinter import font
import matplotlib
import pkg_resources
import datetime
import random
import math
import requests

try:
  matplotlib.use('TkAgg')
except:
  pass
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.pyplot as plt

import numpy as np

support_dir = 'models/support/'
SQRT3 = math.sqrt(3.0)
fontchoice=('Segoe UI', 16)
monochoice=('Courier', fontchoice[1])
boldchoice=(fontchoice[0], fontchoice[1], 'bold')

class DERConfigGUI:
  def __init__(self, master):
    self.master = master
    self.master.protocol('WM_DELETE_WINDOW', self.on_closing)

    self.nb = ttk.Notebook(master)
    self.nb.pack(fill='both', expand='yes')

    s = ttk.Style()
    s.configure('.', font=fontchoice)

    for key, row in i2x.solarChoices.items():
      fname = pkg_resources.resource_filename (__name__, support_dir + row['file'])
      row['data'] = np.loadtxt (fname)
      row['npts'] = row['data'].shape[0]
      peak = max(np.abs(row['data']))
      row['data'] /= peak
    for key, row in i2x.loadChoices.items():
      if 'file' in row:
        fname = pkg_resources.resource_filename (__name__, support_dir + row['file'])
        row['data'] = np.loadtxt (fname)
        row['npts'] = row['data'].shape[0]
        peak = max(np.abs(row['data']))
        row['data'] /= peak

    self.f1 = ttk.Frame(self.nb, name='varsNet')
    lab = ttk.Label(self.f1, text='Feeder Model: ', relief=tk.RIDGE)
    lab.grid(row=0, column=0, sticky=tk.NSEW)
    self.cb_feeder = ttk.Combobox(self.f1, values=[i for i in i2x.feederChoices], name='cbFeeders', font=fontchoice)
    self.cb_feeder.set(next(iter(i2x.feederChoices)))
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
    self.cb_solar = ttk.Combobox(self.f3, values=[i for i in i2x.solarChoices], name='cbSolars', font=fontchoice)
    self.cb_solar.set(next(iter(i2x.solarChoices)))
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
    self.cb_load = ttk.Combobox(self.f4, values=[i for i in i2x.loadChoices], name='cbLoads', font=fontchoice)
    self.cb_load.set(next(iter(i2x.loadChoices)))
    self.cb_load.grid(row=0, column=1, sticky=tk.NSEW)
    self.cb_load.bind('<<ComboboxSelected>>', self.UpdateLoadProfile)
    lab = ttk.Label(self.f4, text='Load Multiplier: ', relief=tk.RIDGE)
    lab.grid(row=0, column=2, sticky=tk.NSEW)
    self.ent_load_mult = ttk.Entry(self.f4, name='load_mult', font=fontchoice)
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
    self.cb_inverter = ttk.Combobox(self.f5, values=[i for i in i2x.inverterChoices], name='cbInverters', font=fontchoice)
    self.cb_inverter.set(next(iter(i2x.inverterChoices)))
    self.cb_inverter.grid(row=0, column=1, sticky=tk.NSEW)
    self.cb_inverter.bind('<<ComboboxSelected>>', self.UpdateInverterMode)
    lab = ttk.Label(self.f5, text='Power Factor: ', relief=tk.RIDGE)
    lab.grid(row=0, column=2, sticky=tk.NSEW)
    self.ent_inv_pf = ttk.Entry(self.f5, name='inv_pf', font=fontchoice)
    self.ent_inv_pf.insert(0, '1.0')
    self.ent_inv_pf.grid(row=0, column=3, sticky=tk.NSEW)
    self.f5.columnconfigure(0, weight=0)
    self.f5.columnconfigure(1, weight=0)
    self.f5.columnconfigure(2, weight=0)
    self.f5.columnconfigure(3, weight=1)
    self.f5.rowconfigure(0, weight=0)
    self.f5.rowconfigure(1, weight=1)
    self.fig_inverter = plt.figure(figsize=(5, 4), dpi=100)
    self.ax_inverter = self.fig_inverter.add_subplot()
    self.ax_inverter.set_xlabel('Voltage [pu]')
    self.ax_inverter.set_ylabel('Power [pu]')
    self.canvas_inverter = FigureCanvasTkAgg(self.fig_inverter, master=self.f5)
    self.canvas_inverter.get_tk_widget().grid(row=1, columnspan=4, sticky=tk.W + tk.E + tk.N + tk.S)
    self.canvas_inverter.draw()
    self.UpdateInverterMode(None)

    self.f6 = ttk.Frame(self.nb, name='varsOutput')
    lab = ttk.Label(self.f6, text='Solution Mode', relief=tk.RIDGE)
    lab.grid(row=0, column=0, sticky=tk.NSEW)
    self.cb_soln_mode = ttk.Combobox(self.f6, values=i2x.solutionModeChoices, name='cbSolutionMode', font=fontchoice)
    self.cb_soln_mode.grid(row=0, column=1, sticky=tk.NSEW)
    self.cb_soln_mode.set('DAILY')
    lab = ttk.Label(self.f6, text='Control Mode', relief=tk.RIDGE)
    lab.grid(row=0, column=2, sticky=tk.NSEW)
    self.cb_ctrl_mode = ttk.Combobox(self.f6, values=i2x.controlModeChoices, name='cbControlMode', font=fontchoice)
    self.cb_ctrl_mode.grid(row=0, column=3, sticky=tk.NSEW)
    self.cb_ctrl_mode.set('STATIC')
    lab = ttk.Label(self.f6, text='Stop Time [min]:', relief=tk.RIDGE)
    lab.grid(row=1, column=0, sticky=tk.NSEW)
    self.ent_stop = ttk.Entry(self.f6, name='stop', font=fontchoice)
    self.ent_stop.insert(0, '1440')
    self.ent_stop.grid(row=1, column=1, sticky=tk.NSEW)
    lab = ttk.Label(self.f6, text='Time Step [s]:', relief=tk.RIDGE)
    lab.grid(row=1, column=2, sticky=tk.NSEW)
    self.ent_step = ttk.Entry(self.f6, name='step', font=fontchoice)
    self.ent_step.insert(0, '300')
    self.ent_step.grid(row=1, column=3, sticky=tk.NSEW)
    self.output_details = tk.IntVar()
    self.output_details.set(1)
    self.cbk_detail = tk.Checkbutton(self.f6, text='Output PV Details', variable=self.output_details, font=fontchoice)
    self.cbk_detail.grid(row=2, column=0, sticky=tk.NSEW)
    self.output_clear = tk.IntVar()
    self.output_clear.set(1)
    self.cbk_clear = tk.Checkbutton(self.f6, text='Clear Old Output', variable=self.output_clear, font=fontchoice)
    self.cbk_clear.grid(row=2, column=1, sticky=tk.NSEW)
    self.btn_run = tk.Button(self.f6, text='Run', command=self.RunOpenDSS, font=boldchoice, bg='blue', fg='white')
    self.btn_run.grid(row=2, column=2, sticky=tk.NSEW)
    self.btn_version = tk.Button(self.f6, text='Check for Updates', command=self.CheckLatestVersion, font=fontchoice, bg='cyan')
    self.btn_version.grid(row=2, column=3, sticky=tk.NSEW)
    self.lab_relay = ttk.Label(self.f6, text='   Relay Trips', relief=tk.RIDGE, justify=tk.RIGHT)
    self.lab_relay.grid(row=3, column=0, sticky=tk.NSEW)
    self.lab_vmin = ttk.Label(self.f6, text='      Vmin pu', relief=tk.RIDGE, justify=tk.RIGHT)
    self.lab_vmin.grid(row=3, column=1, sticky=tk.NSEW)
    self.lab_vmax = ttk.Label(self.f6, text='      Vmax pu', relief=tk.RIDGE, justify=tk.RIGHT)
    self.lab_vmax.grid(row=3, column=2, sticky=tk.NSEW)
    self.lab_vdiff = ttk.Label(self.f6, text='      Vdiff %', relief=tk.RIDGE, justify=tk.RIGHT)
    self.lab_vdiff.grid(row=3, column=3, sticky=tk.NSEW)
    self.lab_een = ttk.Label(self.f6, text='      EEN %', relief=tk.RIDGE, justify=tk.RIGHT)
    self.lab_een.grid(row=3, column=4, sticky=tk.NSEW)
    self.lab_ue = ttk.Label(self.f6, text='      UE %', relief=tk.RIDGE, justify=tk.RIGHT)
    self.lab_ue.grid(row=3, column=5, sticky=tk.NSEW)
    self.txt_output = scrolledtext.ScrolledText(self.f6, font=monochoice)
    self.txt_output.grid(row=4, columnspan=6, sticky=tk.W + tk.E + tk.N + tk.S)
    self.f6.rowconfigure (0, weight=0)
    self.f6.rowconfigure (1, weight=0)
    self.f6.rowconfigure (2, weight=0)
    self.f6.rowconfigure (3, weight=0)
    self.f6.rowconfigure (4, weight=1)
    self.f6.columnconfigure (0, weight=0)
    self.f6.columnconfigure (1, weight=0)
    self.f6.columnconfigure (2, weight=0)
    self.f6.columnconfigure (3, weight=0)
    self.f6.columnconfigure (4, weight=0)
    self.f6.columnconfigure (5, weight=1)

    self.no_error_style = ttk.Style()
    self.no_error_style.configure('Black.TLabel', foreground='black')
    self.error_style = ttk.Style()
    self.error_style.configure('Red.TLabel', foreground='red')

    self.nb.add(self.f1, text='Network', underline=0, padding=2)
    self.nb.add(self.f2, text='DER', underline=0, padding=2)
    self.nb.add(self.f3, text='Solar', underline=0, padding=2)
    self.nb.add(self.f4, text='Loads', underline=0, padding=2)
    self.nb.add(self.f5, text='Inverters', underline=0, padding=2)
    self.nb.add(self.f6, text='Output', underline=0, padding=2)

  def on_closing(self):
    self.master.quit()
    self.master.destroy()
#    if messagebox.askokcancel('Quit', 'Do you want to close this window? It will stop all simulations.'):
#      self.master.quit()
#      self.master.destroy()

  def CheckEntries(self, load_mult, stop_minutes, step_seconds, inv_pf, soln_mode):
    errors = []
    if soln_mode == 'DAILY':
      if (stop_minutes < 1) or (stop_minutes > 1440):
        errors.append ('In DAILY mode, Stop Minutes {:d} must be greater than 0 and no more than 1440'.format (stop_minutes))
      if (step_seconds < 1) or (step_seconds > 300):
        errors.append ('In DAILY mode, Step Seconds {:d} must be greater than 0 and no more than 300'.format (step_seconds))
    elif soln_mode == 'DUTY':
      if (stop_minutes < 1) or (stop_minutes > 1440):
        errors.append ('In DUTY mode, Stop Minutes {:d} must be greater than 0 and no more than 60'.format (stop_minutes))
      if (step_seconds < 1) or (step_seconds > 300):
        errors.append ('In DUTY mode, Step Seconds {:d} must be greater than 0 and no more than 5'.format (step_seconds))
    if (load_mult <= 0.0) or (load_mult > 1.0):
      errors.append ('Load Multiplier {:.4f} must be greater than 0.0 and no more than 1.0'.format (load_mult))
    if (abs(inv_pf) < 0.9153) or (abs(inv_pf) > 1.0):
      errors.append ('Inverter Power Factor {:.4f} must have magnitude between 0.9153 and 1.0, inclusive'.format (inv_pf))
    if len(errors) > 0:
      messagebox.showerror('Please Correct these Errors', '\n'.join(errors))
      return False
    return True

  def CollectDERChanges(self):
    bValid = True
    large_total = 0.0
    rooftop_total = 0.0
    change_lines = []
    errors = []
    pct_roofs = float(self.ent_pct_roofs.get())
    if (pct_roofs < 0.0) or (pct_roofs > 100.0):
      errors.append ('% Rooftops {:.4f} must lie between 0 and 100, inclusive'.format(pct_roofs))
    else:
      pu_roofs = pct_roofs * 0.01
      for key, row in self.graph_dirs["resloads"].items():
        if random.random() <= pu_roofs:
          bus = row['bus']
          kv = row['kv']
          kw = row['derkw']
          kva = kw * 1.21 # TODO: Cat A or Cat B
          rooftop_total += kw
          change_lines.append('new pvsystem.{:s} bus1={:s}.1.2 phases=2 kv={:.3f} kva={:.2f} pmpp={:.2f} irrad=1.0 pf=1.0'.format (key, bus, kv, kva, kw))

    for key, row in self.graph_dirs["largeder"].items():
      print (key, row)
      kw = float(self.f2.nametowidget('kw_{:s}'.format(key)).get())
      large_total += kw
      kva = float(self.f2.nametowidget('kva_{:s}'.format(key)).get())
      dertype = self.f2.nametowidget('type_{:s}'.format(key)).get()
      oldtype = row['type']
      if (kw < 0.0) or (kva < kw):
        errors.append ('{:s} {:s} kw={:.2f} kva={:.2f} must have kw>=0 and kva>=kw'.format(dertype, key, kw, kva))
        bValid = False
      elif dertype == oldtype:  # change the size or dispatch, but not the type
        if dertype == 'solar':
          change_lines.append('edit pvsystem.{:s} kva={:.2f} pmpp={:.2f}'.format(key, kva, kw))
        elif dertype == 'storage':
          change_lines.append('edit storage.{:s} kva={:.2f} kw={:.2f}'.format(key, kva, kw))
        elif dertype == 'generator':
          change_lines.append('edit generator.{:s} kva={:.2f} kw={:.2f}'.format(key, kva, kw))
      else:
        bus = row['bus']
        kv = row['kv']
        # remove the old one
        if oldtype == 'solar':
          change_lines.append('edit pvsystem.{:s} enabled=no'.format(key))
        elif oldtype == 'storage':
          change_lines.append('edit storage.{:s} enabled=no'.format(key))
        elif oldtype == 'generator':
          change_lines.append('edit generator.{:s} enabled=no'.format(key))
        # create a new one
        if dertype == 'solar':
          change_lines.append('new pvsystem.{:s} bus1={:s} kv={:.3f} kva={:.3f} pmpp={:.3f} irrad=1'.format(key, bus, kv, kva, kw))
        elif dertype == 'storage':
          change_lines.append('new storage.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f}'.format(key, bus, kv, kva, kw))
        elif dertype == 'generator':
          change_lines.append('new generator.{:s} bus1={:s} kv={:.3f} kva={:.3f} kw={:.3f}'.format(key, bus, kv, kva, kw))

    if len(errors) > 0:
      messagebox.showerror('Please Correct these DER Entries', '\n'.join(errors))
      bValid = False
    return bValid, large_total, rooftop_total, change_lines

  def get_pv_kv_base(self, name):
    kvnom = 0.120
    if name in self.graph_dirs["pvder"]:
      row = self.graph_dirs["pvder"][name]
      kvnom = row['kv']
      if row['phases'] > 1:
        kvnom /= SQRT3
    elif name in self.graph_dirs["largeder"]: # maybe user changed the type from generator or storage
      row = self.graph_dirs["largeder"][name]
      kvnom = row['kv']
      if row['phases'] > 1:
        kvnom /= SQRT3
    return kvnom

  def update_entry(self, ctl, val):
    ctl.delete(0, tk.END)
    ctl.insert(0, val)

  def clear_label(self, lbl, text):
    lbl.config(text=text)
    lbl.configure(style='Black.TLabel')

  def failed_label(self, lbl):
    lbl.config(text='FAILED')
    lbl.configure(style='Red.TLabel')

  def update_label(self, lbl, val, fmt, thresh):
    valstr = fmt.format(val)
    color = 'Black.TLabel'
    if thresh >= 0 and val > thresh:
      color = 'Red.TLabel'
    if thresh < 0 and val < abs(thresh):
      color = 'Red.TLabel'
    lbl.config(text=valstr)
    lbl.configure(style=color)

  def RunOpenDSS(self):
    load_mult = float(self.ent_load_mult.get())
    feeder_choice = self.cb_feeder.get()
    soln_mode = self.cb_soln_mode.get()
    ctrl_mode = self.cb_ctrl_mode.get()
    solar_profile = self.cb_solar.get()
    load_profile = self.cb_load.get()
    inv_mode = self.cb_inverter.get()
    inv_pf = float(self.ent_inv_pf.get())
    stop_minutes = int(self.ent_stop.get())
    step_seconds = int(self.ent_step.get())
    num_steps = int (60 * stop_minutes / step_seconds)
    if not self.CheckEntries(load_mult, stop_minutes, step_seconds, inv_pf, soln_mode):
      return
    der_valid, large_total, rooftop_total, change_lines = self.CollectDERChanges()
    if not der_valid:
      return

    if self.output_clear.get() > 0:
      self.txt_output.delete('1.0', tk.END)

    print (feeder_choice, solar_profile, load_mult, load_profile, inv_mode, inv_pf,
           soln_mode, ctrl_mode, step_seconds, num_steps)
    d = i2x.run_opendss(choice = feeder_choice,
                        pvcurve = solar_profile,
                        loadmult = load_mult,
                        loadcurve = load_profile,
                        invmode = inv_mode,
                        invpf = inv_pf, 
                        stepsize = step_seconds, 
                        numsteps = num_steps,
                        ctrlmode = ctrl_mode,
                        solnmode = soln_mode,
                        change_lines = change_lines)
    self.txt_output.insert(tk.END, 'Analysis Run on {:s} at {:s}'.format(feeder_choice, datetime.datetime.now().strftime('%a %d-%b-%Y %H:%M:%S')))
    self.txt_output.insert(tk.END, '  Large DER={:.2f} kW, Rooftop PV={:.2f} kW\n'.format(large_total, rooftop_total))
    self.txt_output.insert(tk.END, '  LoadMult={:.4f}, LoadProfle={:s}\n'.format(load_mult, load_profile))
    self.txt_output.insert(tk.END, '  SolarProfile={:s}, InvMode={:s}, InvPF={:.3f}\n'.format(solar_profile, inv_mode, inv_pf))
    self.txt_output.insert(tk.END, 'Number of Capacitor Switchings = {:d}\n'.format(d['num_cap_switches']))
    self.txt_output.insert(tk.END, 'Number of Tap Changes = {:d}\n'.format(d['num_tap_changes']))
    self.txt_output.insert(tk.END, 'Number of Relay Trips = {:d}\n'.format(d['num_relay_trips']))

    if not d['converged']:
      self.txt_output.insert(tk.END, 'Solution Failed to Converge!')
      for lbl in [self.lab_vmin, self.lab_vmax, self.lab_vdiff, self.lab_een, self.lab_ue]:
        self.failed_label (lbl)
      return

    self.txt_output.insert(tk.END, '{:d} Nodes with Low Final Voltage, Lowest={:.4f}pu at {:s}\n'.format(d['num_low_voltage'], d['vminpu'], d['node_vmin']))
    self.txt_output.insert(tk.END, '{:d} Nodes with High Final Voltage, Highest={:.4f}pu at {:s}\n'.format(d['num_high_voltage'], d['vmaxpu'], d['node_vmax']))

    self.update_label (self.lab_relay, d['num_relay_trips'], '{:d} relay trips', 0)

    if soln_mode == 'SNAPSHOT':
      self.update_label (self.lab_vmin, d['vminpu'], 'Vmin={:.4f} pu', -0.95)
      self.update_label (self.lab_vmax, d['vmaxpu'], 'Vmax={:.4f} pu', 1.05)
      self.clear_label (self.lab_vdiff, 'Vdiff %')
      self.clear_label (self.lab_een, 'EEN %')
      self.clear_label (self.lab_ue, 'UE %')
      return

    base = d['kWh_Load']
    pctSource = 0.0
    pctLosses = 0.0
    pctGeneration = 0.0
    pctSolar = 0.0
    pctUE = 0.0
    pctEEN = 0.0
    if base > 0.0:
      pctSource = 100.0 * d['kWh_Net'] / base
      pctLosses = 100.0 * d['kWh_Loss'] / base
      pctGeneration = 100.0 * d['kWh_Gen'] / base
      pctSolar = 100.0 * d['kWh_PV'] / base
      pctEEN = 100.0 * d['kWh_EEN'] / base
      pctUE = 100.0 * d['kWh_UE'] / base
    pctReactive = 0.0
    if d['kWh_PV'] > 0.0:
      pctReactive = abs(100.0 * d['kvarh_PV'] / d['kWh_PV'])
    self.txt_output.insert(tk.END, 'Load Served =               {:11.2f} kWh\n'.format(d['kWh_Load']))
    self.txt_output.insert(tk.END, 'Substation Energy =         {:11.2f} kWh, {:.4f}% of Load\n'.format(d['kWh_Net'], pctSource))
    self.txt_output.insert(tk.END, 'Losses =                    {:11.2f} kWh, {:.4f}% of Load\n'.format(d['kWh_Loss'], pctLosses))
    self.txt_output.insert(tk.END, 'Generation =                {:11.2f} kWh, {:.4f}% of Load\n'.format(d['kWh_Gen'], pctGeneration))
    self.txt_output.insert(tk.END, 'Solar Output =              {:11.2f} kWh, {:.4f}% of Load\n'.format(d['kWh_PV'], pctSolar))
    self.txt_output.insert(tk.END, 'Solar Reactive Energy =     {:11.2f} kvarh, {:.4f}% of P\n'.format(d['kvarh_PV'], pctReactive))
    self.txt_output.insert(tk.END, 'Energy Exceeding Normal =   {:11.2f} kWh, {:.4f}% of Load\n'.format(d['kWh_EEN'], pctEEN))
    self.txt_output.insert(tk.END, 'Unserved Energy =           {:11.2f} kWh, {:.4f}% of Load\n'.format(d['kWh_UE'], pctUE))
#    self.txt_output.insert(tk.END, 'Normal Overload Energy =    {:11.2f} kWh\n'.format(d['kWh_OverN']))
#    self.txt_output.insert(tk.END, 'Emergency Overload Energy = {:11.2f} kWh\n'.format(d['kWh_OverE']))

    pv_vmin = 100.0
    pv_vmax = 0.0
    pv_vdiff = 0.0
    for key, row in d['pvdict'].items():
      v_base = 1000.0 * self.get_pv_kv_base (key)
      row['vmin'] /= v_base
      row['vmax'] /= v_base
      row['vmean'] /= v_base
      row['vdiff'] /= v_base
      row['vdiff'] *= 100.0
      if row['vmin'] < pv_vmin:
        pv_vmin = row['vmin']
      if row['vmax'] > pv_vmax:
        pv_vmax = row['vmax']
      if row['vdiff'] > pv_vdiff:
        pv_vdiff = row['vdiff']
    self.txt_output.insert(tk.END, 'Minimum PV Voltage        = {:.4f} pu\n'.format(pv_vmin))
    self.txt_output.insert(tk.END, 'Maximum PV Voltage        = {:.4f} pu\n'.format(pv_vmax))
    self.txt_output.insert(tk.END, 'Maximum PV Voltage Change = {:.4f} %\n'.format(pv_vdiff))

    self.update_label (self.lab_vmin, pv_vmin, 'Vmin={:.4f} pu', -0.95)
    self.update_label (self.lab_vmax, pv_vmax, 'Vmax={:.4f} pu', 1.05)
    self.update_label (self.lab_vdiff, pv_vdiff, 'Vdiff={:.4f} %', 2.0)
    self.update_label (self.lab_een, pctEEN, 'EEN={:.3f} %', 0.0)
    self.update_label (self.lab_ue, pctUE, 'UE={:.3f} %', 0.0)

    if self.output_details.get() > 0:
      self.txt_output.insert(tk.END, 'PV Name                    kWh     kvarh     Vmin     Vmax    Vmean Vdiff[%]\n')
      for key, row in d['pvdict'].items():
        self.txt_output.insert(tk.END, '{:20s} {:9.2f} {:9.2f} {:8.4f} {:8.4f} {:8.4f} {:8.4f}\n'.format(key, row['kWh'], row['kvarh'], 
                                                                               row['vmin'], row['vmax'], row['vmean'], row['vdiff']))


  def ResetDERPage(self):
    for w in self.f2.grid_slaves():
      w.grid_forget()

    pvkw = 0.0
    pvkva = 0.0
    npv = len(self.graph_dirs["pvder"])
    for key, row in self.graph_dirs["pvder"].items():
      pvkw += row['kw']
      pvkva += row['kva']

    genkw = 0.0
    genkva = 0.0
    ngen = len(self.graph_dirs["gender"])
    for key, row in self.graph_dirs["gender"].items():
      genkw += row['kw']
      genkva += row['kva']

    batkw = 0.0
    batkva = 0.0
    nbat = len(self.graph_dirs["batder"])
    for key, row in self.graph_dirs["batder"].items():
      batkw += row['kw']
      batkva += row['kva']

    lab_load = ttk.Label(self.f2, text='Total Load = {:.2f} kW'.format(self.graph_dirs["loadkw"]), relief=tk.RIDGE)
    lab_load.grid(row=0, column=0, sticky=tk.NSEW)
    lab_pv = ttk.Label(self.f2, text='Existing Solar = {:.2f} kVA, {:.2f} kW in {:d} units'.format(pvkva, pvkw, npv), relief=tk.RIDGE)
    lab_pv.grid(row=1, column=0, sticky=tk.NSEW)
    lab_bat = ttk.Label(self.f2, text='Existing Storage = {:.2f} kVA, {:.2f} kW in {:d} units'.format(batkva, batkw, nbat), relief=tk.RIDGE)
    lab_bat.grid(row=2, column=0, sticky=tk.NSEW)
    lab_gen = ttk.Label(self.f2, text='Existing Generation = {:.2f} kVA, {:.2f} kW in {:d} units'.format(genkva, genkw, ngen), relief=tk.RIDGE)
    lab_gen.grid(row=3, column=0, sticky=tk.NSEW)
    lab_roofs = ttk.Label(self.f2, text='{:d} Available Residential Rooftops, Use [%]:'.format(len(self.graph_dirs["resloads"])), relief=tk.RIDGE)
    lab_roofs.grid(row=4, column=0, sticky=tk.NSEW)
    self.ent_pct_roofs = ttk.Entry(self.f2, name='pct_roofs', font=fontchoice)
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
    for key, row in self.graph_dirs["largeder"].items():
      lab = ttk.Label(self.f2, text='Name={:s} Bus={:s} kV={:.2f} kW={:.2f} kVA={:.2f} Type={:s}'.format (key,
                                                                                                          row['bus'],
                                                                                                          row['kv'],
                                                                                                          row['kw'],
                                                                                                          row['kva'],
                                                                                                          row['type']), 
                      relief=tk.RIDGE)
      lab.grid(row=idx, column=0, sticky=tk.NSEW)
      e1 = ttk.Entry(self.f2, name='kw_{:s}'.format(key), font=fontchoice)
      e1.insert(0, str(row['kw']))
      e1.grid(row=idx, column=1, sticky=tk.NSEW)
      e2 = ttk.Entry(self.f2, name='kva_{:s}'.format(key), font=fontchoice)
      e2.insert(0, str(row['kva']))
      e2.grid(row=idx, column=2, sticky=tk.NSEW)
      cb1 = ttk.Combobox(self.f2, values=['solar','storage','generator'], name='type_{:s}'.format(key), font=fontchoice)
      cb1.set(row['type'])
      cb1.grid(row=idx, column=3, sticky=tk.NSEW)
      idx += 1

  def UpdateFeeder(self, event):
    key = self.cb_feeder.get()
    row = i2x.feederChoices[key]
    self.feeder_name = key
    self.feeder_path = row['path']
    self.feeder_base = row['base']
    fname = pkg_resources.resource_filename (__name__, row['path'] + row['network'])
    self.G = i2x.load_opendss_graph(fname)

    self.graph_dirs = i2x.parse_opendss_graph(self.G)
    # self.pvder, self.gender, self.batder, self.largeder, self.resloads, bus3phase, self.loadkw = i2x.parse_opendss_graph(self.G)

    self.ax_feeder.cla()
    i2x.plot_opendss_feeder (self.G, plot_labels=True, on_canvas=True, 
                             ax=self.ax_feeder, fig=self.fig_feeder)
    self.canvas_feeder.draw()
    self.ResetDERPage()

  def UpdateSolarProfile(self, event):
    key = self.cb_solar.get()
    row = i2x.solarChoices[key]
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
    row = i2x.loadChoices[key]
    if 'dt' in row:
      dt = row['dt']
      npts = row['npts']
      tmax = dt * (npts - 1)
      p = row['data']
      t = np.linspace (0.0, tmax, npts) / 3600.0
    else:
      t = row['t']
      p = row['p']
    self.ax_load.cla()
    self.ax_load.plot(t, p, color='blue')
    self.ax_load.set_xlabel('Hour [pu]')
    self.ax_load.set_ylabel('Power [pu]')
    self.ax_load.set_xticks(ticks)
    self.ax_load.set_xlim(ticks[0], ticks[-1])
    self.ax_load.grid()
    self.canvas_load.draw()

  def UpdateInverterMode(self, event):
    ticks = [0.90, 0.92, 0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.08, 1.10]
    key = self.cb_inverter.get()
    row = i2x.inverterChoices[key]
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

  def CheckLatestVersion(self):
    resp = requests.get('https://pypi.org/pypi/i2x/json')
    if resp.status_code == 200:
      jtext = resp.json()
      pypi_version = jtext['info']['version']
      my_version = i2x.__version__
      advice = ''
      status = 'equal'
      if my_version < pypi_version:
        status = 'newer'
        advice = '\nuse "pip install i2x --upgrade" if you wish to upgrade'
      elif my_version > pypi_version:
        status = 'older'
      messagebox.showinfo('Version Check', 
                          'You have version {:s}\nLatest release version is {:s}, {:s}{:s}'.format(my_version,
                                                                                                   status, 
                                                                                                   pypi_version,
                                                                                                   advice))
    else:
      messagebox.showwarning('Version Check', 
                             'Unable to reach pypi.org for the latest released version number')

  # resp = requests.get("https://pypi.org/simple/i2x")
  # assert resp.status_code == 200
  # text = resp.text
  # print (text)

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
  root.title('i2x Test Systems: DER Cases: v{:s}'.format(i2x.__version__))
  bigfont = font.Font(family=fontchoice[0],size=fontchoice[1])
  root.option_add("*Font", bigfont)
  root.option_add("*TCombobox*Listbox*Font", bigfont)
  root.option_add("*Dialog.msg.font", bigfont)
  my_gui = DERConfigGUI(root)
  while True:
    try:
      root.mainloop()
      break
    except UnicodeDecodeError:
      pass

if __name__ == "__main__":
  show_der_config()
