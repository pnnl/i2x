#!/usr/bin/env python
# coding: utf-8
#
# This code contains the modules which will actaully perform the temperature calculations
# based on the transformer thermal class and operating conditions using differential equation solvers.
#
# This file is part of IEEE C57.91 2024 project which is released under BSD-3-Clause.
# See file LICENSE.md or go to https://opensource.ieee.org/inslife/ieee-c57.91-2024/ for full license details.

from scipy.integrate import odeint, solve_ivp
from scipy.interpolate import interp1d
import transformer_thermal_models.constants as constants
import numpy as np
import pandas as pd

def calculate_tau_to(cooling_system,T_tor,P_w,P_e,P_s,P_c,M_cc,M_tank,liquid_volume):

    P_t = P_w + P_e + P_s + P_c

    if cooling_system.upper() in ['ONAN','ONAF']:
        C = 0.06 * M_cc + 0.04 * M_tank + 1.33 * liquid_volume
    elif cooling_system.upper() in ['OFAF','ODAF']:
        C = 0.06 * M_cc + 0.06 * M_tank + 1.93 * liquid_volume
    else:
        C = None

    tau_to = C * T_tor / P_t * 60

    return tau_to

def old_clause_7(time_segment,load,T_amb,cooling_system,P_w,P_e,P_s,P_c,T_tor,T_hsr,tau_to,T_to_i,T_hs_i,tau_w,n,m):

    T_to_i -= T_amb[0]
    T_hs_i -= T_amb[0]

    R = (P_w + P_e + P_s) / P_c

    T_tou = T_tor * ((load ** 2 * R + 1) / (R + 1)) ** n

    T_to = (T_tou - T_to_i) * (1 - np.exp(- time_segment / tau_to)) + T_to_i

    T_hsu = (T_hsr - T_tor) * load ** (2 * m)

    T_hs = (T_hsu - (T_hs_i-T_to_i)) * (1 - np.exp(- time_segment / tau_w)) + (T_hs_i-T_to_i)

    return T_to+T_amb,T_hs+T_to+T_amb

def clause_7_alternative(t, delta_T, Load_profile, T_ambient_profile, T_tor, T_hsr, R, tau_to, tau_w, n, m):

    T_to = delta_T[0]
    T_hs = delta_T[1]

    load = Load_profile(t)
    T_amb = T_ambient_profile(t)

    #Draft Eq 26
    delta_T_to = (T_tor * ((1+load**2*R)/(1+R))**n - (T_to - T_amb) ) / tau_to

    #Draft Eq 27
    delta_T_hs = ((T_hsr-T_tor) * (load**(2*m)) - (T_hs - T_to)) / tau_w

    return delta_T_to,delta_T_hs

def ieee_c57_91_main_clause_7(Transformer,LoadConditions):
    
    MVA_rated = Transformer.MVA_rated
    MVA_loss = Transformer.MVA_loss
    T_loss = Transformer.T_loss
    P_wr = Transformer.P_wr
    P_er = Transformer.P_er
    P_sr = Transformer.P_sr
    P_cr = Transformer.P_cr
    P_coe = Transformer.P_coe
    E_hs = Transformer.E_hs
    M_cc = Transformer.M_cc
    M_tank = Transformer.M_tank
    liquid_volume = Transformer.liquid_volume
    T_ambr = Transformer.T_ambr
    T_wg = Transformer.T_wg
    T_wr = Transformer.T_wr
    T_hsr = Transformer.T_hsr
    T_tor = Transformer.T_tor
    T_bor = Transformer.T_bor
    T_k = Transformer.T_k
    H_hs = Transformer.H_hs
    tau_w = Transformer.tau_w
    cooling_system = Transformer.cooling_system
    winding_material = Transformer.winding_material
    liquid_type = Transformer.liquid_type
    
    time = LoadConditions.time
    T_ambient = LoadConditions.T_ambient
    load = LoadConditions.load
    
    # Correct temperature "rises" for "above ambient"
    T_wg += T_ambr
    T_wr += T_ambr
    T_hsr += T_ambr
    T_tor += T_ambr
    T_bor += T_ambr

    # Initialize starting temperatures for model based on rated temperatures

    #G.3.3 Text on duct top-liquid temperature at rated load
    if cooling_system.upper() in ['ONAN','ONAF','ODAF']:
        T_tdor = T_tor
    elif 'OFAF' in cooling_system.upper():
        T_tdor = (T_tor+T_bor)/2

    # Caluculated Rated Temperatures
    ## Added by Tim
    T_aor = (T_tor+T_bor)/2
    T_daor = (T_tdor+T_bor)/2
    T_wor = H_hs * (T_tdor - T_bor) + T_bor

    # Additional equations to make a better guess at the initial temperatures
    # Allows for cold start-up temperatures and quicker convergence
    ## Added by Zack
    def adjust_initial_temp(T,L,T_A,T_AR):
        return (T-T_AR)*L+T_A

    T_ao = adjust_initial_temp(T_aor,load[0],T_ambient[0],T_ambr)
    T_w = adjust_initial_temp(T_wr,load[0],T_ambient[0],T_ambr)
    T_wo = adjust_initial_temp(T_wr,load[0],T_ambient[0],T_ambr)
    T_hs = adjust_initial_temp(T_hsr,load[0],T_ambient[0],T_ambr)
    T_to = adjust_initial_temp(T_tor,load[0],T_ambient[0],T_ambr)
    T_bo = adjust_initial_temp(T_bor,load[0],T_ambient[0],T_ambr)
    T_tdo = adjust_initial_temp(T_tdor,load[0],T_ambient[0],T_ambr)

    # Correct "rated" losses against "measured" losses
    ## Added by Tim
    x = (MVA_rated/MVA_loss)**2
    t = (T_k + T_wg)/(T_k + T_loss)
    P_w = x * P_wr * t
    P_e = x * P_er / t
    P_s = x * P_sr / t
    P_c = P_cr

    # Making some assumptions about hotspot losses
    ## Added by Tim
    T_khs = (T_hsr+T_k)/(T_wg+T_k)
    P_whs = P_w * T_khs
    P_ehs = P_e / P_w

    #Overwriting initial temperatures

    def Q_gen_windings(K,P_x,P_y,T_x,T_xr,T_k):
        #Equation G.5 (x=w) & G.15 (x=hs)
        K_x = (T_x + T_k)/(T_xr + T_k)

        #Equation G.4 (x=w, y=e) & G.15 (x=hs, y=ehs)
        Q = K**2 * ((P_x * K_x) + (P_y / K_x))

        return Q

    def Q_lost_windings(cooling_system,liquid_type,P_z,P_x,T_x,T_xr,T_y,T_yr):
        
        # Added by Zack
        # T_x-T_y can be negative at low load values which creates an imaginary number
        # Since equation is scaling relationship, solution was to take absolute value and 
        # then multiply by the sign function at the end.

        if cooling_system.upper() in ['ONAN','ONAF','OFAF','OFAF1','OFAF2']:
            #Equation G.6A (x=w, y=dao, z=e) & G.16A (x=hs, y=wo, z=ehs)
            mu_xr = liquid_viscosity((T_xr+T_yr)/2,liquid_type)
            mu_x = liquid_viscosity((T_x+T_y)/2,liquid_type)

            Q = ((np.abs(T_x-T_y)/(T_xr-T_yr))**1.25)*((mu_xr/mu_x)**0.25)*(P_z+P_x)

        elif cooling_system.upper() in ['ODAF']:
            #Equation G.6B (x=w, y=dao, z=e) & G.16B (x=hs, y=wo, z=ehs)
            Q = (np.abs(T_x-T_y)/(T_xr-T_yr))*(P_z+P_x)

        return np.sign(T_x-T_y)*Q

    def average_liquid_specific_heat_capacity(M_tank,M_core,M_liquid,liquid_type):

        #FIXME Allow for other tank and core material types
        Cp_tank = constants.specific_heat['steel']
        Cp_core = constants.specific_heat['steel']
        Cp_liquid = constants.specific_heat[liquid_type.lower()]

        #Equation G.24
        M_ao_Cp_ao = (M_tank*Cp_tank) + (M_core*Cp_core) + (M_liquid*Cp_liquid)

        return M_ao_Cp_ao

    def liquid_viscosity(T,liquid_type):

        D = constants.D_table[liquid_type.lower()]

        G = constants.G_table[liquid_type.lower()]

        #Equation G.28
        mu = D*np.exp(G/(T+273.15))

        return mu


    #Eq. G.12
    P_hs = ((T_hsr+T_k)/(T_hsr+T_k))*P_w

    #Eq. G.13
    P_ehs = E_hs*P_hs

    M_w_Cp_w = ((P_w + P_e)*tau_w) / (T_wr-T_daor)

    #Eq. G.22
    M_w = M_w_Cp_w / constants.specific_heat[liquid_type.lower()]

    #Eq. G.23
    M_core = M_cc - M_w

    M_liquid = liquid_volume * constants.liquid_density[liquid_type.lower()]

    #Eq. G.24
    M_ao_Cp_ao = average_liquid_specific_heat_capacity(M_tank,M_core,M_liquid,liquid_type)
    
    def differential_equations(t, delta_T, cooling_system, Load_profile, T_amb_pro, overexcited_pro):
    
        T_w = delta_T[0]
        T_tdo = delta_T[1]
        T_wo = delta_T[2]
        T_hs = delta_T[3]
        T_ao = delta_T[4]
        T_to = delta_T[5]
        T_bo = delta_T[6]

        T_dao = (T_tdo+T_bo)/2

        # Load time dependent variables
        ##  added by Zack to make differential equations work in solver
        K = Load_profile(t)
        T_amb = T_amb_pro(t)
        
        oe = 0
        if overexcited_pro:
            # Adjust exponents for core being overexcited
            ## added by Zack
            oe = overexcited_pro(t)

        # Look up values in Tables of Annex G
        x = constants.duct_liquid_rise_exponent[cooling_system]
        y = constants.average_liquid_rise_exponent[cooling_system]
        z = constants.to_bo_rise_exponent[cooling_system]

        # A.3.2 Average Winding Temperature

        Q_gen_w = Q_gen_windings(K,P_w,P_e,T_w,T_wr,T_k)

        Q_lost_w = Q_lost_windings(cooling_system,liquid_type,P_e,P_w,T_w,T_wr,T_dao,T_daor)

        delta_T_w = (Q_gen_w-Q_lost_w)/M_w_Cp_w

        # A.3.3 Winding duct liquid temperature rise over bottom liquid temperature
        #Eq. G.9
        delta_T_tdo_bo  = np.sign(Q_lost_w)*(((np.abs(Q_lost_w)/(P_w+P_e))**x)*(T_tdor-T_bor))
        # equation modified by Zack to handle sqrt of a negative number since Q_lost_w can be negative.
 
        ## Added "- (T_tdo-T_bo)" by Zack to keep in differential form instead of "rise" temperature
        delta_T_tdo = delta_T_tdo_bo - (T_tdo-T_bo)

        #Eq. G.10
        ## Added " - (T_wo-T_bo)" by Zack to keep in differential form instead of "rise" temperature
        delta_T_wo_bo = H_hs * (T_tdo-T_bo) - (T_wo-T_bo)

        # A.3.4 Winding hottest-spot temperature

        #Eq. G.14
        Q_gen_hs = Q_gen_windings(K,P_hs,P_ehs,T_hs,T_hsr,T_k)

        #Eq. G.15 + 16A + 16B
        Q_lost_hs = Q_lost_windings(cooling_system,liquid_type,P_ehs,P_hs,T_hs,T_hsr,T_wo,T_wor)

        #Eq. G.17
        delta_T_hs = (Q_gen_hs-Q_lost_hs)/M_w_Cp_w

        # A.3.5 Average liquid temperature

        #Eq. G.18
        if oe == 1.0:
            Q_core = P_coe
            P_c = P_coe
        else:
            Q_core = P_cr
            P_c = P_cr

        #Eq. G.19
        K_w = (T_w + T_k)/(T_wr + T_k)

        Q_stray_loss = (K**2 * P_s)/K_w

        #Eq. G.20
        P_t = P_w + P_e + P_s + P_c

        #Eq. G.21
        Q_lost_liquid = np.sign(T_ao - T_amb)*((np.abs(T_ao - T_amb) / (T_aor - T_ambr))**(1/y)) * P_t
        # modified to handle imaginary numbers (ambient temp is greater than average oil temp)

        #Eq. G.25
        delta_T_ao = (Q_lost_w + Q_stray_loss + Q_core - Q_lost_liquid)/(M_ao_Cp_ao)

        # A.3.6 Top and Bottom Liquid

        #Eq. G.26
        delta_T_to_bo = np.sign(Q_lost_liquid)*((np.abs(Q_lost_liquid)/P_t)**z) * (T_tor - T_bor)
        # modified to handle imaginary numbers (heat gained from ambient environment)

        ## Added " - (T_to-T_bo)" # Added by Zack to keep in differnetial form instead of "rise" temperature
        delta_T_to = (delta_T_to_bo)-(T_to-T_bo)
        delta_T_bo = -1*((delta_T_to_bo)-(T_to-T_bo))

        delta_T_to += delta_T_ao
        delta_T_bo += delta_T_ao

        #Eq. G.11
        delta_T_wo = delta_T_wo_bo
        #delta_T_wo = (T_to-T_bo) - (T_wo-T_bo)
        if T_tdo < T_to:
            delta_T_wo = (T_to-T_bo) - (T_wo-T_bo)
            #delta_T_wo = delta_T_to

        ## Added by Zack
        # Solution is unstable during cold start ups and load spikes.
        # Default behavior is to change to the delta temperature of windings temporarily.
        # When solution is not degenerate, normal equations should take over.

        if not np.isfinite(delta_T_w):
            delta_T_w = 0

        if not np.isfinite(delta_T_tdo):    
            delta_T_tdo = delta_T_w

        if not np.isfinite(delta_T_wo): 
            delta_T_wo = delta_T_w

        if not np.isfinite(delta_T_hs): 
            #print('HS degenerate: ',delta_T_hs,t/60,K)
            delta_T_hs = delta_T_w

        if not np.isfinite(delta_T_ao): 
            #print('AO degenerate: ',delta_T_ao,t/60,K)
            delta_T_ao = delta_T_w/2
            delta_T_to = delta_T_w
            delta_T_bo = 0

        #Return delta temperatures to differnetial solver
        return (delta_T_w, delta_T_tdo, delta_T_wo, delta_T_hs, delta_T_ao, delta_T_to, delta_T_bo)

    args=(cooling_system,
          LoadConditions.Load_profile,
          LoadConditions.T_ambient_profile,
          LoadConditions.Overexcited_profile,
         )
    
    #Uses new SciPy API
    #ts = pyt.time()

    #Explicit Runge-Kutta methods (‘RK23’, ‘RK45’, ‘DOP853’) should be used for non-stiff problems and implicit methods (‘Radau’, ‘BDF’) for stiff problems [9]. Among Runge-Kutta methods, ‘DOP853’ is recommended for solving with high precision (low values of rtol and atol).
    #If not sure, first try to run ‘RK45’. If it makes unusually many iterations, diverges, or fails, your problem is likely to be stiff and you should use ‘Radau’ or ‘BDF’. ‘LSODA’ can also be a good universal choice, but it might be somewhat less convenient to work with as it wraps old Fortran code.
    # time_sol = np.linspace(int(time[0]),int(time[-1]),int(time[-1]-time[0])*6)
    # Converting back to seconds in num argument to make sure we have 6 samples per second.
    time_sol = np.linspace(time[0],time[-1],int((time[-1]-time[0])*60)*6)

    output = solve_ivp(differential_equations, (time[0], time[-1]), [T_w, T_tdo, T_wo, T_hs, T_ao, T_to, T_bo], args=args, method='RK45', t_eval=time_sol, dense_output=True)

    solution = output.y
    time_sol = output.t

    #print('Execution time: ',pyt.time()-ts,'\n')
    
    columns=['Time [Minutes]','Winding [C]','Duct Liquid [C]','Winding Liquid [C]','Hot Spot [C]','Average [C]','Top Liquid [C]','Bottom Liquid [C]']
    
    output_table = pd.DataFrame(np.transpose(np.vstack((time_sol,solution))),columns=columns)
    
    return output_table


def ieee_c57_91_alt_clause_7(Transformer,LoadConditions):
    # Clause 7 using differntial equations
    # Effectively Annex G with several restrictive assumptions made for simplification
    
    MVA_rated = Transformer.MVA_rated
    MVA_loss = Transformer.MVA_loss
    T_wg = Transformer.T_wg
    T_loss = Transformer.T_loss
    T_k = Transformer.T_k
    T_ambr = Transformer.T_ambr
    P_wr = Transformer.P_wr
    P_er = Transformer.P_er
    P_sr = Transformer.P_sr
    P_cr = Transformer.P_cr
    P_coe = Transformer.P_coe
    T_hsr = Transformer.T_hsr
    T_tor = Transformer.T_tor
    M_cc = Transformer.M_cc
    M_tank = Transformer.M_tank
    liquid_volume = Transformer.liquid_volume
    cooling_system = Transformer.cooling_system
    tau_w = Transformer.tau_w
    
    time = LoadConditions.time
    T_ambient = LoadConditions.T_ambient
    load = LoadConditions.load

    # Correct "rated" losses versus "measured" losses
    x = (MVA_rated/MVA_loss)**2
    t = (T_k + T_wg)/(T_k + T_loss)

    P_w = x * P_wr * t
    P_e = x * P_er / t
    P_s = x * P_sr / t
    P_c = P_cr

    def adjust_initial_temp(T,L,T_A,T_AR):
        return (T-T_AR)*L+T_A

    # Initialize temperatures for model based on rated temperatures
    in_T_hs = adjust_initial_temp(T_hsr,load[0],T_ambient[0],T_ambr)
    in_T_to = adjust_initial_temp(T_tor,load[0],T_ambient[0],T_ambr)
    
    Load_profile = interp1d(time, load, kind='linear', fill_value='extrapolate')
    T_ambient_profile = interp1d(time, T_ambient, fill_value='extrapolate')

    n = constants.n_exponent[cooling_system.upper()]
    m = constants.m_exponent[cooling_system.upper()]

    R = (P_w + P_e + P_s) / P_c
    
    tau_to = calculate_tau_to(cooling_system,T_tor,P_w,P_e,P_s,P_c,M_cc,M_tank,liquid_volume)
    
    args=(
      LoadConditions.Load_profile,
      LoadConditions.T_ambient_profile,
      T_tor, 
      T_hsr,
      R,
      tau_to,
      tau_w,
      n,
      m,
    )
    
    #Uses new SciPy API
    #ts = pyt.time()

    #Explicit Runge-Kutta methods (‘RK23’, ‘RK45’, ‘DOP853’) should be used for non-stiff problems and implicit methods (‘Radau’, ‘BDF’) for stiff problems [9]. Among Runge-Kutta methods, ‘DOP853’ is recommended for solving with high precision (low values of rtol and atol).
    #If not sure, first try to run ‘RK45’. If it makes unusually many iterations, diverges, or fails, your problem is likely to be stiff and you should use ‘Radau’ or ‘BDF’. ‘LSODA’ can also be a good universal choice, but it might be somewhat less convenient to work with as it wraps old Fortran code.
    # time_sol = np.linspace(int(time[0]),int(time[-1]),int(time[-1]-time[0])*6)
    # Converting back to seconds in num argument to make sure we have 6 samples per second.
    time_sol = np.linspace(time[0],time[-1],int((time[-1]-time[0])*60)*6)

    output = solve_ivp(clause_7_alternative, (time[0], time[-1]), [in_T_to, in_T_hs], args=args, method='RK45', t_eval=time_sol, dense_output=True)

    solution = output.y
    time_sol = output.t

    #print('Execution time: ',pyt.time()-ts,'\n')
    
    columns=['Time [Minutes]','Top Liquid [C]','Hot Spot [C]']
    
    output_table = pd.DataFrame(np.transpose(np.vstack((time_sol,solution))),columns=columns)
    
    return output_table


def ieee_c57_91_old_clause_7_analytical(Transformer,LoadConditions):
    
    MVA_rated = Transformer.MVA_rated
    MVA_loss = Transformer.MVA_loss
    T_wg = Transformer.T_wg
    T_loss = Transformer.T_loss
    T_k = Transformer.T_k
    T_ambr = Transformer.T_ambr
    P_wr = Transformer.P_wr
    P_er = Transformer.P_er
    P_sr = Transformer.P_sr
    P_cr = Transformer.P_cr
    P_coe = Transformer.P_coe
    T_hsr = Transformer.T_hsr
    T_tor = Transformer.T_tor
    M_cc = Transformer.M_cc
    M_tank = Transformer.M_tank
    liquid_volume = Transformer.liquid_volume
    cooling_system = Transformer.cooling_system
    tau_w = Transformer.tau_w
    
    time = LoadConditions.time
    T_ambient = LoadConditions.T_ambient
    load = LoadConditions.load

    # Correct "rated" losses versus "measured" losses
    x = (MVA_rated/MVA_loss)**2
    t = (T_k + T_wg)/(T_k + T_loss)

    P_w = x * P_wr * t
    P_e = x * P_er / t
    P_s = x * P_sr / t
    P_c = P_cr

    def adjust_initial_temp(T,L,T_A,T_AR):
        return (T-T_AR)*L+T_A

    # Initialize temperatures for model based on rated temperatures
    T_hs_i = adjust_initial_temp(T_hsr,load[0],T_ambient[0],T_ambr)
    T_to_i = adjust_initial_temp(T_tor,load[0],T_ambient[0],T_ambr)
    
    Load_profile = interp1d(time, load, kind='linear', fill_value='extrapolate')
    T_ambient_profile = interp1d(time, T_ambient, fill_value='extrapolate')
    
    # time_sol = np.linspace(int(time[0]),int(time[-1]),int(time[-1]-time[0]))
    # Converting back to seconds in num argument since fractional minutes allowed
    time_sol = np.linspace(time[0],time[-1],int((time[-1]-time[0])*60))
    
    # For the analytical solution to work, you need to loop over the time periods where steps in load occurs
    
    load_sol = Load_profile(time_sol)
    T_amb_sol = T_ambient_profile(time_sol)
    
    idx = np.where(np.diff(load_sol,prepend=load[0]) != 0)[0]
    idx = np.append(idx,len(load_sol))
    idx = np.append(0,idx)

    ranges = [(idx[i-1],idx[i]) for i in np.arange(len(idx))[1:]]

    solution = [np.array([]),np.array([])]
    
    tau_to = calculate_tau_to(cooling_system,T_tor,P_w,P_e,P_s,P_c,M_cc,M_tank,liquid_volume)
    
    n = constants.n_exponent[cooling_system.upper()]
    m = constants.m_exponent[cooling_system.upper()]

    for r in ranges:
        solution_segment = old_clause_7(
            time_sol[r[0]:r[1]]-time_sol[r[0]],
            load_sol[r[0]:r[1]],
            T_amb_sol[r[0]:r[1]],
            cooling_system,P_w,P_e,P_s,P_c,T_tor,T_hsr,tau_to,T_to_i,T_hs_i,tau_w,n,m)

        T_to_i = solution_segment[0][-1]#-T_ambient[r[0]:r[1]][-1]
        T_hs_i = solution_segment[1][-1]#-T_ambient[r[0]:r[1]][-1]

        solution[0] = np.append(solution[0],solution_segment[0])
        solution[1] = np.append(solution[1],solution_segment[1])

    columns = ['Time [Minutes]', 'Top Liquid [C]', 'Hot Spot [C]']
    
    output_table = pd.DataFrame(np.transpose(np.vstack((time_sol,tuple(solution)))),columns=columns)
    
    return output_table

AVAILABLE_METHODS = {
                    'main_clause_7_diff':ieee_c57_91_main_clause_7, # old Annex G, rewritten in differential equations
                    'alt_clause_7_diff':ieee_c57_91_alt_clause_7, # new Clause 7, simplified for lack of bottom rated tempratures
                    'old_clause_7_analytical':ieee_c57_91_old_clause_7_analytical, # old Clause 7
                  }

def solve_temperatures(Transformer,LoadConditions,method):
    
    selected_method = AVAILABLE_METHODS.get(method, None)

    if selected_method:
        solution = selected_method(Transformer,LoadConditions)
    else:
        assert False, method + '" method not supported.'

    Transformer.solution = solution
    Transformer.method = method

    return Transformer