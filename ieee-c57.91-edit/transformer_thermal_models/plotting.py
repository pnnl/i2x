#!/usr/bin/env python
# coding: utf-8
#
# This code contains methods of plotting the results from the temperature calculations
# such that they can be interpreted more easily.
#
# This file is part of IEEE C57.91 2024 project which is released under BSD-3-Clause.
# See file LICENSE.md or go to https://opensource.ieee.org/inslife/ieee-c57.91-2024/ for full license details.

import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
from matplotlib import colors
import numpy as np

def plot_max_hotspot(Transformer,max_hotspot_table):
    
    df = max_hotspot_table['Max Hotspot Table']
    time_interval = max_hotspot_table['Overload Time Interval']
    method = max_hotspot_table['Method']
    
    T_hsr = Transformer.T_hsr+Transformer.T_ambr
    T_bit = Transformer.T_bit
    
    ambient = df.columns.values
    load = df.index.values
    values = df.values
    
    rated_hs = Transformer.T_hsr+Transformer.T_ambr
    
    divnorm=colors.TwoSlopeNorm(vcenter=rated_hs)
    fig, ax = plt.subplots(figsize=(8,6), dpi=300)
    im = ax.imshow(values, cmap='RdYlGn_r', norm=divnorm, aspect='auto')

    ax.set_yticks(np.arange(len(load)))
    ax.set_xticks(np.arange(len(ambient)))

    ax.set_yticklabels(load, rotation=45, ha="right",
             rotation_mode="anchor")
    ax.set_xticklabels(ambient)
    
    ax.set_xlabel(r'Avg. Ambient Temperature [$^{\circ}$C]')
    ax.set_ylabel('Load [P.U.]')
    
    ax.set_ylim(-0.5,len(load)-0.5)
    ax.set_xlim(-0.5,len(ambient)-0.5)
    
    for i in range(len(load)):
        for j in range(len(ambient)):
            text = ax.text(j, i, values[i, j],
                           ha="center", va="center", color="black", backgroundcolor='w', fontsize=7)

    ax.set_title("Max Hotspot Temperature")

    def temp_border_line(twod_arr):
        sz = np.shape(twod_arr)

        x = []
        y = []

        for j,col in enumerate(np.transpose(twod_arr)):         
                #print(row)
                #print(col)

                idx2 = np.where(col > 0)[0]

                if idx2.any():
                    x+=[j]
                    y+=[np.min(idx2)-0.5]
        
        x=[x[0]-0.5]+x+[x[-1]+0.5]
        y=[y[0]]+y+[y[-1]]
        
        return x,y

    if T_bit:
        bit = values > T_bit
        x,y = temp_border_line(bit)
        ax.plot(x,y,'c',label='BIT',lw=4)

    hsrt = values > T_hsr

    x,y = temp_border_line(hsrt)
    ax.plot(x,y,'m',label=r'$T_{hsr}$',lw=4)

    cb = plt.colorbar(im)
    ax1 = cb.ax
    ax1.axhline(T_hsr,0,1,color='m',linewidth=4)
    
    if T_bit:
        ax1.axhline(T_bit,0,1,color='c',linewidth=4)

    ax.legend(bbox_to_anchor=[-0.05,1.1])
    
    # table to convert method to plain text
    method_text = {
        "main_clause_7_diff":"Main C7 (RK45)",
        "alt_clause_7_diff":"Alt C7 (RK45)",
        "old_clause_7_analytical":"Old C7 (Analytical)",  
    }

    textstr = [ 
        [
            r'Method used: %s' % (method_text[method], ),
            r'Initial Load: %s [1]' % (max_hotspot_table['Initial Load'], ),
            r'Average WCP: %s [%%]' % (Transformer.WCP),
            #r'Time Interval: %s [min]' % (time_interval, ),
            r'Time Interval: %s [sec]' % (time_interval, ),
        ],
        [
            r'Rated $T_{hotspot}: %s$ [$^{\circ}$C]' % (T_hsr, ),
            r'Max Rated Power: %s [MVA]' % (Transformer.MVA_rated),
            r'Cooling System: %s' % (Transformer.cooling_system, ),
            r'Calculated $T_{BIT}: %s$ [$^{\circ}$C]' % (T_bit, ),
        ],
    ]
    
    table_height = np.shape(textstr)[0]*0.07

    table = plt.table(cellText=textstr,cellLoc='center',bbox=[-0.18, -0.2-table_height, 1.28, table_height])
    
    table.auto_set_font_size(False)
    table.set_fontsize(8)

    fig.tight_layout()
    
    return plt.gcf()


def plot_results(Transformer,LoadConditions):
    fig, axs = plt.subplots(2,1, figsize=(8,6), dpi=300, sharex=True, gridspec_kw={'height_ratios': [3.5, 1]})
    fig.subplots_adjust(hspace=0)

    solution = Transformer.solution
    #time_sol = solution['Time [Minutes]']
    time_sol = solution['Time [seconds]']
    
    T_ambient_profile = LoadConditions.T_ambient_profile
    Load_profile = LoadConditions.Load_profile

    T_hsr = Transformer.T_hsr+Transformer.T_ambr
    T_tor = Transformer.T_tor+Transformer.T_ambr

    #time_hours = time_sol/60

    T_amb_for_plot = T_ambient_profile(time_sol)
    
    axs[0].plot(time_sol,T_ambient_profile(time_sol),label='Amb')
    
    col_names = solution.columns.values
    
    if 'Bottom Liquid [C]' in solution.columns:       
        axs[0].plot(time_sol,solution['Winding [C]'],label='Winding',lw=0.5)
        axs[0].plot(time_sol,solution['Duct Liquid [C]'],label='Top-of-Duct Liquid',ls='-.',lw=0.5)
        axs[0].plot(time_sol,solution['Winding Liquid [C]'],label='Winding Liquid',ls=':',lw=0.5)
        axs[0].plot(time_sol,solution['Hot Spot [C]'],label='Hot Spot',ls='--',lw=0.5)
        axs[0].plot(time_sol,solution['Average [C]'],label='Average',lw=0.5)
        axs[0].plot(time_sol,solution['Top Liquid [C]'],label='Top',lw=0.5)
        axs[0].plot(time_sol,solution['Bottom Liquid [C]'],label='Bottom',lw=0.5)
        axs[0].set_ylim([0,np.round(np.nanmax(np.max(solution['Hot Spot [C]']))+40)])
    else:
        axs[0].plot(time_sol,solution['Top Liquid [C]'],label='Top',lw=0.5)
        axs[0].plot(time_sol,solution['Hot Spot [C]'],label='Hot Spot',ls='--',lw=0.5)
        axs[0].set_ylim([0,np.round(np.nanmax(np.max(solution['Hot Spot [C]']))+40)])

        
    y1 = np.round(np.nanmax(T_amb_for_plot)-5)
    y2 = np.round(np.nanmax(solution['Hot Spot [C]'])+40)

    if y1 < T_hsr < y2:
        axs[0].axhline(T_hsr,0,max(time_sol),color='k',ls='--',alpha=0.5,lw=0.5)
        axs[0].text(0,T_hsr+1,'HS',fontsize=7)

    if y1 < T_tor < y2:
        axs[0].axhline(T_tor,0,max(time_sol),color='k',ls='--',alpha=0.5,lw=0.5)
        axs[0].text(0,T_tor+1,'TO',fontsize=7)

    axs[0].legend(loc=2,ncol=4)
    axs[0].set_ylabel('Temp [°C]')

    axs[0].xaxis.set_major_locator(MultipleLocator(10))
    axs[0].xaxis.set_minor_locator(AutoMinorLocator(5))

    axs[0].yaxis.set_major_locator(MultipleLocator(25))
    axs[0].yaxis.set_minor_locator(AutoMinorLocator(5))

    plot_load = Load_profile(time_sol)
    axs[1].plot(time_sol,plot_load-0.035,label='Load',color='gold')

    axs[1].set_ylim([-0.07,round(max(plot_load)+0.85,1)])
    axs[1].set_ylabel('Variables')

    axs[1].xaxis.set_major_locator(MultipleLocator(10))
    axs[1].xaxis.set_minor_locator(AutoMinorLocator(5))

    axs[1].yaxis.set_major_locator(MultipleLocator(0.5))
    axs[1].yaxis.set_minor_locator(AutoMinorLocator(2))

    axs[1].legend(loc=2,ncol=4)
    axs[0].set_title('Transformer Temperatures vs Load Model')
    #axs[1].set_xlabel('Time [minutes]')
    axs[1].set_xlabel('Time [seconds]')

    cooling_system_variations = Transformer.cooling_system

    textstr = [
        [
            r'Cooling System: %s' % (cooling_system_variations, ),
            r'Winding Material: %s' % (Transformer.winding_material.upper(), ),
            r'Liquid Type: %s' % (Transformer.liquid_type.upper(), )
        ],
        [
            r'Rated $T_{ambient}: %s$' % (Transformer.T_ambr, ),
            r'Rated $T_{windings}: %s$' % (Transformer.T_wr+Transformer.T_ambr, ),
            r'Rated $T_{hotspot}: %s$' % (Transformer.T_hsr+Transformer.T_ambr, )  
        ],
        [
            r'Height of Hotspot: %s' % (Transformer.H_hs, ),
            r'Energy of Hotspot: %s' % (Transformer.E_hs, ),
            r'Winding Timing: %s' % (Transformer.tau_w, )  
        ],
        [
            r'P$_{winding}: %s$' % (Transformer.P_wr, ),
            r'P$_{eddy}: %s$' % (Transformer.P_er, ),
            r'P$_{stray}: %s$' % (Transformer.P_sr, )  
        ],
        [
            r'P$_{core}: %s$' % (Transformer.P_cr, ),
            r'P$_{core\;overexcited}: %s$' % (Transformer.P_coe, ),
            ''
        ],
    ]

    axs[0].set_xlim([0,max(time_sol)])
    axs[1].set_xlim([0,max(time_sol)])

    table_height = np.shape(textstr)[0]*0.17
    
    axs[1].table(cellText=textstr,rowLoc='center',bbox=[0.05, -0.5-table_height, 0.90, table_height])

    return plt.gcf()
