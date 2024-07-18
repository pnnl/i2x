import pyomo.environ as pyo
import numpy as np
import pandas as pd
import argparse, sys, os
import tomli
from typing import Union
from i2x.der_hca.hca import print_config
import copy
import plotly.io as pio
import re

pd.options.plotting.backend = "plotly"
pio.templates.default = "plotly_white"

PLOTLY_LAYOUT = {"font_size": 20, "font_family":"Arial", 
                 "width":800, "height":600,
                 "legend": dict(x=0.5, y=1, xanchor="center", yanchor="bottom", orientation="h")}

def main(bes_kw:float, bes_kwh:float, f:np.ndarray, hc:np.ndarray,
         energy_price:Union[float, np.ndarray]=1.0,
         print_model=False, solver="cbc", **kwargs):
    """
    returns:
    df_fixed: data frame with input forecast an hosting capacity
    df_vars: data frame with variables
    """
    
    model = pyo.ConcreteModel()
    
    hrs = list(range(len(hc)))
    model.n_hrs = len(hrs)
    model.f = f
    model.hc = hc
    model.overgen = f -  np.vstack([f, hc]).min(axis=0)
    if isinstance(energy_price,float):
        model.energy_price = energy_price * np.ones((model.n_hrs,), dtype=float)
    elif isinstance(energy_price, np.ndarray):
        model.energy_price = energy_price

    ## battery output
    model.bess_chr = pyo.Var(hrs, bounds=(0, bes_kw))
    model.bess_dis = pyo.Var(hrs, bounds=(0, bes_kw))
    model.bess_chr_notovergen = pyo.Var(hrs)
    model.E = pyo.Var(hrs, bounds=(0,bes_kwh))
    model.curt = pyo.Var(hrs, bounds=(0, None))
    model.u = pyo.Var(hrs, domain=pyo.Binary) # 1: discharge, 0: charge

    @model.Constraint(hrs)
    def curtailment_rule(model,h):
        """if overgeneration is 0, so is curtailment"""
        return model.curt[h] <= model.overgen[h]
    
    @model.Constraint(hrs)
    def charge_from_overgen_rule(model,h):
       """total bess charging minus charging from non overgeneration solar plus curtailment
       is the totalover generation
       Case 1: no overgeneration
        * curtialment is 0 due to curtailment_rule
        * all charging is not from overgen
        Case 2: some overgen
        * curtailment is 0
        * total charge is reduced by overgen to equal charging from not overgen
        Case 3: some overgen
        * curtailment is non 0
        * any remaining overhead is reduced from total charge to yield charge not from overgen"""
       return model.bess_chr[h] - model.bess_chr_notovergen[h] + model.curt[h] ==  model.overgen[h]
    @model.Constraint(hrs)
    def discharge_rule(model,h):
        return model.bess_dis[h] <= bes_kw*model.u[h]
    @model.Constraint(hrs)
    def charge_rule(model,h):
        return model.bess_chr[h] <= bes_kw*(1-model.u[h])
    @model.Constraint(hrs)
    def soc_rule(model, h):
        """battery state of charge change"""
        return model.E[h] == model.E[(h-1) % model.n_hrs] - model.bess_dis[h] + model.bess_chr[h]

    @model.Constraint(hrs)
    def no_gridcharge_rule(model, h):
        """Power output is >=0 (no charging from grid)"""
        return model.f[h] - model.bess_chr[h] >= 0
    
    # ## curtailment is forecast minus hosting capacity 
    # ## **if** hosting capacity is less than forecast,
    # ## otherwise zero
    # model.curt = f - np.vstack([f, hc]).min(axis=0)

    # @model.Constraint([h for h in hrs if model.curt[h] == 0])
    @model.Constraint(hrs)
    def output_rule(model, h):
        """forecast + bess_discharge - bess_charge - curtailment <= hosting capacity"""
        return model.bess_dis[h] - model.bess_chr[h] + model.f[h] - model.curt[h] <= model.hc[h]
    
    @model.Objective(sense=pyo.maximize)
    def obj(model):
        """
        Objective is to maximize battery discharge while minimizing cost
        from charging the battery during non overgeneration period.

        """
        # M = 10 * model.energy_price.max()
        # return sum(model.energy_price[h]*(model.f[h] + model.bess_dis[h] - model.bess_chr_notovergen[h] - model.curt[h]) for h in hrs) 
        return sum(model.energy_price[h]*(model.bess_dis[h] - model.bess_chr_notovergen[h]) for h in hrs)
                #    M*model.curt[h] for h in hrs)
    # @model.Objective(sense=pyo.minimize)
    # def obj(model):
    #     """objective is to maximize charging (minimize negative injection) 
    #     during hours where curtailment would occur.
    #     curtailment without BESS is f - min(f, hc), which will be >= 0.
    #     Hours where curtailment would occur are those where curtailment > 0
    #     """
    #     return sum(model.bess[h] for h in hrs if model.curt[h] > 0)

    opt = pyo.SolverFactory(solver)
    
    opt.solve(model, tee=True)
    if print_model:
        model.pprint()
    
    #### Collect variables
    ## form https://stackoverflow.com/questions/67491499/how-to-extract-indexed-variable-information-in-pyomo-model-and-build-pandas-data
    vars = [pd.Series(f, name="forecast"),
            pd.Series(hc, name="HC"),
            pd.Series(model.overgen, name="overgen")]
    all_vars = model.component_map(ctype=pyo.Var)
    for k,v in all_vars.items():
        vars.append(pd.Series(v.extract_values(), name=k))

    df_vars = pd.concat(vars, axis=1)

    output = (df_vars["bess_dis"] - df_vars["bess_chr"] + df_vars["forecast"] - df_vars["curt"]).rename("output")
    pvtot  = (df_vars["forecast"] - df_vars["curt"]).rename("pv_total")
    pvexp  = (pvtot - df_vars["bess_chr"]).rename("pv_export")
    bess_chr_overgen = (df_vars["bess_chr"] - df_vars["bess_chr_notovergen"]).rename("bess_chr_overgen")
    # curt = (output - np.vstack([output, hc]).min(axis=0)).rename("curtailment")
    # output -= curt
    ## add output 
    # df_vars = pd.concat([df_vars, output, curt], axis=1)
    df_vars = pd.concat([df_vars, output, pvtot, pvexp, bess_chr_overgen], axis=1)

    curt_no_bess = f -  np.vstack([f, hc]).min(axis=0)
    output_no_bess = f - curt_no_bess
    df_fixed = pd.DataFrame({"forecast": f, "HC": hc, 
                             "output_no_bess": output_no_bess, "curtailment_no_bess": curt_no_bess })
    
    return df_fixed, df_vars

def no_fix_case(f:np.ndarray, hc:np.ndarray):
    """
    scenario where capacity is limited to the minimum HC
    return the capacity and a data frame with all values
    """

    hc_min = np.floor(hc.min()) # minimum HC
    cap_in = f.max()            # rating of input profile
    fnew = f*(hc_min/cap_in)   # scale profile to have a max of hc_min --> no curtailment

    curt = fnew - np.vstack([fnew, hc]).min(axis=0) # should be zero
    output = fnew - curt # should be equal to fnew
    return hc_min, pd.DataFrame({"forecast": fnew, "HC": hc, "curtailment": curt, "output": output})


def load_data_profile(filepath:str, profile_col, sheet_name=None, index_col=0) -> np.ndarray:
    """
    Load a profile from file (excel or csv).

    profile col is the column name of the profile to read

    sheet_name: None -> implies csv, otherwise excel sheetname
    index_col: index_column to pandas.read_csv or pandas.read_excel
    """
    if sheet_name is None:
        return pd.read_csv(filepath, index_col=index_col)[profile_col].values
    else:
        return pd.read_excel(filepath, sheet_name=sheet_name, index_col=index_col)[profile_col].values


def inadvertent_export_delta(rsc, xsc, kvbase_ll, pf=1, rvc_limit=0.03, 
                             hc:np.ndarray=None, f:np.ndarray=None):
    """
    Calculate maximum capacity above hosting capacity considering 
    Inadvertent export limit

    From BATRIES/IEEE Std 1453-2022
    (Rsc x dP - Xsc x dQ)/V^2 <= 0.03 (rvc_lim)

    where dP = (DER Rating - HC) * PF
    dQ = (DER Rating - HC) * sqrt(1 - PF^2)

    therefore,
                                            (V [kV])^2
    (DER Rating - HC) [kW] = 0.03 * ---------------------------------------- * 1000
                                   Rsc [Ohm] * PF - Xsc [Ohm] * sqrt(1-PF^2)
    """

    dpmax = rvc_limit*1000*np.power(kvbase_ll,2)/(rsc*pf - xsc*np.sqrt(1 - pf**2))
    
    print(f"Max DER Rating - HC = {dpmax:0.1f} kW")
    if hc is not None:
        print(f"Min HC = {hc.min():0.1f} kW")
        max_der_opt1 = hc.min() + dpmax
        print(f"Max DER (Option 1): {max_der_opt1:0.1f} kW")
        if f is not None:
            max_der_opt2 = max_capacity_detailed(dpmax, f, hc)
            # print(np.max(f - hc))
            # max_der_opt2 = dpmax/np.abs(np.max(f - hc))
            print(f"Max DER (Option 2): {max_der_opt2:0.1f} kW")
            print(f"Option 2 verification: {(max_der_opt2*unitize(f) - hc).max(): 0.1f} kW")

def max_capacity_detailed(dpmax:float, f:np.ndarray, hc:np.ndarray, solver="cbc"):

    model = pyo.ConcreteModel()
    
    hrs = list(range(len(hc)))
    model.f = unitize(f)
    model.hc = hc

    ## battery output
    model.c = pyo.Var(bounds=(0, None))
    
    @model.Constraint(hrs)
    def pmax_rule(model, h):
        """capacity minus hc <= dpmax"""
        return model.c*model.f[h] - model.hc[h] <= dpmax
    
    @model.Objective(sense=pyo.maximize)
    def obj(model):
        """
        objective is to maximize capacity respecting inadvertent export limit
        """
        return model.c

    opt = pyo.SolverFactory(solver)
    
    opt.solve(model)#, tee=True)
    return pyo.value(model.c)

def unitize(f:np.ndarray) -> np.ndarray:
    """
    Return a unitized version of f
    """
    return f/f.max()

def profile_stats(x:np.ndarray, name=""):
    """
    display statistics for array x
    """
    print(f"{name}profile statistics:")
    print(f"\tlength\t{x.shape[0]}")
    print(f"\tmin\t{x.min():.1f}")
    print(f"\tavg\t{x.mean():.1f}")
    print(f"\tmax\t{x.max():.1f}")
    print(f"\tq[10,25,50,75,90]\t{np.round(np.percentile(x,[10,25,50,75,90]),1)}")

def time_index(year, n=8760) -> pd.DatetimeIndex:
    return pd.date_range(start=f"{year}-01-01", periods=n, freq="h")

def add_time_index(df:pd.DataFrame, tidx:pd.DatetimeIndex=None, year:int=None,
                   add_month_col = False) -> pd.DataFrame:

    
    if tidx is None:
        if year is None:
            year = pd.to_datetime("now").year
        tidx = time_index(year, n=df.shape[0])

    df = df.set_axis(tidx, axis=0)
    columns = list(df.columns)
    if add_month_col:
        df["month"] = tidx.month.values
        columns = ["month"] + columns
    return df.loc[:, columns]

def value_summary(dfdata:pd.Series, dfprice:pd.DataFrame, quantity_name="kWh"):
    # if ~isinstance(dfdata.index, pd.DatetimeIndex):
    #     dfdata = add_time_index(dfprice)
    # if ~isinstance(dfprice.index, pd.DatetimeIndex):
    #     dfprice = add_time_index(dfprice)

    out = pd.concat([dfdata.groupby(lambda x: x.month).agg("sum").rename(quantity_name),
            dfprice.mul(dfdata, axis=0).groupby(lambda x: x.month).agg("sum")],
            axis=1)
    
    return out

def annualized_cost(capex:float, om:float, discount:float, escalation:float, years:int) -> Union[float,np.ndarray]:

    ### annualized cost is:
    ##          r(1 + r)^years                r
    ## capex * --------------- = capex *  -----------------
    ##         (1+r)^years - 1             1 - (1+r)^-years

    c_ann = capex * discount/(1 - np.power(1+discount, -years))
    
    if om == 0:
        return c_ann
    else:
        return c_ann + om*np.power(1+escalation, np.arange(years))

def npv(rate:float, cash_flow:np.ndarray) -> float:
    """Return the Net Present Value for the values in cash_flow:
        NPV = sum cash_flow[i]/(1 + rate)^i
    where i goes from 0 to the length of cash_flow - 1

    Args:
        rate (float): discount rate
        cash_flow (np.ndarray): cash flow values

    Returns:
        float: Net Present Value
    """

    return sum( v/np.power(1+rate, i) for i, v in enumerate(cash_flow))

def annual_benefit(val:Union[float, np.ndarray], degredation:float, escalation:float, years:int):
    
    return val*np.power(1 - degredation, np.arange(years))*np.power(1+escalation, np.arange(years))

def calc_capex_and_om(dollar_per_kw, dollar_per_kw_year, kw, capex_reduce_fraction=0):
    capex = dollar_per_kw*(1 - capex_reduce_fraction)*kw
    om = dollar_per_kw_year*kw
    return capex, om

def plot_res(data:Union[dict, str], scenarios:list, prop:str, save_path:str):

    if isinstance(data, str):
        #### path to excel file, load the annual results into a dictionary
        filename = data
        data = {}
        with pd.ExcelFile(filename) as book:
            for k in scenarios:
                data[k] = pd.read_excel(book, sheet_name=f"{k} Annual", index_col=0)

    tmp = pd.concat([data[k][prop].rename(k) for k in scenarios], axis=1)

    fig = tmp.plot(labels={"index": "year", "value": prop, "variable": "Scenario" },
                   markers=True)
    fig.update_layout(**PLOTLY_LAYOUT)

    basename = os.path.join(save_path, re.sub("\W+","",prop.replace(" ","_")))

    save_plot(fig, basename)
    # fig.update_layout(title=prop)

def save_plot(fig, basename:str):
    
    ### Save
    fig.write_html(basename+".html", include_plotlyjs="cdn")
    for ext in ["png", "svg"]:
        fig.write_image(f"{basename}.{ext}")

def plot_npv(data:Union[dict,str], save_path:str):

    if isinstance(data,str):
        data = pd.read_excel(data, sheet_name="NPV", index_col=0)

    data1 = data.loc[lambda x: ~x.index.str.contains("Upgrade")]
    data2 = data.loc[lambda x: x.index.str.contains("Upgrade")]

    for d, t in zip([data1,data2], ["npv", "upgrade_npv"]):
        fig = d.plot(kind="bar",
                        labels={"index": "Scenario", "value": "NPV [$]"})
        fig.update_layout(showlegend=False, **PLOTLY_LAYOUT)
        save_plot(fig, os.path.join(save_path, t))

    
    
        
                    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve for optimal BESS utilization given solar profile and hosting capacity results")
    parser.add_argument("configfile", help=".toml configuration")
    parser.add_argument("--plot", help="plot results properties (joined with plot key in config file)", action="append", default=[])
    parser.add_argument("--plot-path", help="path to store plots in (plot_path in config file will override this)", default=".")
    parser.add_argument("--print-hca-stats", help="print hca statistics and exit.", action="store_true")
    parser.add_argument("--rvc-lim", help="calculate limits based on rvc", action="store_true")
    parser.add_argument("--test-input", action="store_true")
    args = parser.parse_args()
    # bes_kw  = 200
    # bes_kwh = 400
    # hc = np.array([1000, 700, 700, 1350.5, 1200.0])
    # f  = np.array([500, 800.0, 1000.0, 850.0, 600.2])
    
    with open(args.configfile, mode='rb') as f:
        configuration = tomli.load(f)
    print_config(configuration, printtype=True)
    input_config = copy.deepcopy(configuration)
    props_to_plot = set(args.plot + configuration.get("plot", []))
    for k in ["hc", "f", "energy_price", "dvr_adjust"]:
        if isinstance(configuration[k], str):
            configuration[k] = load_data_profile(configuration[k], configuration[f"{k}_col"], 
                                configuration.get(f"{k}_sheet_name", None),
                                configuration.get(f"{k}_index_col", 0))
        else:
            configuration[k] = np.array(configuration[k])
    ## apply scaling
    configuration["f"] *= configuration.get("f_scale",1)   # scaling of solar profile
    configuration["hc"] *= configuration.get("hc_scale",1) # scaling of hca result
    print_config(configuration, title="Post Convert Configuration", printtype=True)
    if args.print_hca_stats:
        profile_stats(configuration["hc"], name="HC ")
        profile_stats(configuration["f"], name="PV profile ")
        sys.exit(0)

    if args.rvc_lim:
        inadvertent_export_delta(configuration["rsc"], configuration["xsc"],
                           configuration["kvbase_ll"],
                           pf=configuration.get("pf", 1),
                           rvc_limit=configuration.get("rvc_limit", 0.03),
                           hc=configuration["hc"],
                           f=configuration["f"])
        sys.exit(0)
    if args.test_input:
        print(args)
        print("properties to plot", set(args.plot + configuration.get("plot", [])))
        sys.exit(0)
    if props_to_plot and os.path.exists(configuration["savename"]):
        ### just plot, don't run first
        scenarios = ["FIX+BESS", "FIX"]
        if configuration["run_no_fix"]:
            scenarios.append("No FIX")
        for prop in props_to_plot:
            if prop == "NPV":
                plot_npv(configuration["savename"], configuration.get("plot_path", args.plot_path))
            else:
                plot_res(configuration["savename"], scenarios, prop, configuration.get("plot_path", args.plot_path))
        sys.exit(0)
    
    ########## RUN OPTIMIZATION 
    df_fixed, df_vars = main(**configuration)
    tidx = time_index(configuration.get("study_year", pd.to_datetime("now").year), n=df_fixed.shape[0])
    with pd.ExcelWriter(configuration.get("savename", "bessopt.xlsx")) as writer:
        ### convert to time index
        df_fixed = add_time_index(df_fixed, tidx)
        df_vars = add_time_index(df_vars, tidx)
        
        df_fixed.to_excel(writer, sheet_name="fixed")
        df_vars.to_excel(writer, sheet_name="variables")

        
        if configuration.get("run_no_fix", False):
            no_fix_cap , df_no_fix = no_fix_case(configuration["f"], configuration["hc"])
            df_no_fix = add_time_index(df_no_fix, tidx)
            df_no_fix.to_excel(writer, sheet_name="no_fix")
            input_config["no_fix_cap"] = no_fix_cap
        

        
        ## reload price data and save to output
        df_price = {}
        for k,v in zip(["energy_price", "dvr_adjust"], ["prices", "DVR"]):
            if input_config.get(f"{k}_sheet_name", None) is None:
                df_price[k] = pd.read_csv(input_config[k], 
                                    index_col=input_config.get(f"{k}_index_col", 0))
            else:
                df_price[k] = pd.read_excel(input_config[k], 
                                        sheet_name=input_config[f"{k}_sheet_name"],
                                        index_col=input_config.get(f"{k}_index_col", 0))
            if k == "energy_price":
                df_price[k] = add_time_index(df_price[k], year=configuration.get("study_year", pd.to_datetime("now").year))
            if input_config.get("copy_price_data", False):
                df_price[k].to_excel(writer, sheet_name=v)


        var2label = {"FIX+BESS": 
                        {
                            "pv_export": "DER Output [kWh]", 
                            "curt": "Curtailment [kWh]", 
                            "bess_dis": "BESS Discharge [kWh]",
                            "bess_chr_notovergen": "BESS CHarge from Possible Export [kWh]"
                        },
                    "FIX": 
                        {
                            "output_no_bess": "DER Output [kWh]",
                            "curtailment_no_bess": "Curtailment [kWh]"
                        },
                    "No FIX":
                        {
                            "output": "DER Output [kWh]",
                            "curtailment": "Curtailment [kWh]"
                        }
                    }
        scenario2vars = {"FIX+BESS": df_vars, "FIX": df_fixed}
        if configuration["run_no_fix"]:
            scenario2vars["No FIX"] = df_no_fix
        
        ### Value Summary By Month
        summary_out = {}
        for scenario, mapping in var2label.items():
            startrow = 0
            summary_out[scenario] = {}
            for k,v in mapping.items():
                summary_out[scenario][k] = value_summary(scenario2vars[scenario][k], df_price["energy_price"], quantity_name=v)
                summary_out[scenario][k].to_excel(writer, sheet_name=f"{scenario} ValueByMonth", startrow=startrow)
                startrow += summary_out[scenario][k].shape[0] + 3
                
                ### write total
                summary_out[scenario][k].sum(axis=0).to_frame().T.to_excel(writer,sheet_name=f"{scenario} ValueByMonth", startrow=startrow)
                startrow += 4 # 2 for data, 2 space

        annual_vars = {"FIX+BESS":
                        {   
                            "output": ["pv_export", "bess_dis"],
                            "curtailment": "curt",
                            "capex": ["der", "bess"],
                            "scale": {"der": "f_scale", "bess": "bes_kw"}
                        },
                        "FIX":
                        {
                            "output" : ["output_no_bess"],
                            "curtailment": "curtailment_no_bess",
                            "capex": ["der"],
                            "scale": {"der": "f_scale"}
                        },
                        "No FIX":
                        {
                            "output": ["output"],
                            "curtailment": "curtailment",
                            "capex": ["der"],
                            "scale": {"der": "no_fix_cap"}
                        }
                    }
        #### Annual Summary
        yearly_out = {}
        net_present_value = {}
        for scenario, mapping in var2label.items():
            tmp = {}
            
            tmp["Export [kWh]"] = 0
            tmp["Revenue [$]"] = 0
            #### OUTPUT and REVENUE
            for k in annual_vars[scenario]["output"]:
                annual_output = summary_out[scenario][k].loc[:, var2label[scenario][k]].sum(axis=0).squeeze()
                annual_rev = summary_out[scenario][k].loc[:, configuration["energy_price_col"]].sum(axis=0).squeeze() + \
                                summary_out[scenario][k].loc[:, configuration["dvr_price_col"]].sum(axis=0).squeeze() * (configuration["dvr_adjust"] - 1)
                tmp[var2label[scenario][k]] = annual_benefit(annual_output, 
                                                             configuration["degredation"], 
                                                             0, 
                                                             configuration["capex_years"]) # power output does not consider escalation rate.
                revenue_label = var2label[scenario][k].replace("[kWh]", "Revenue [$]")
                tmp[revenue_label] = annual_benefit(annual_rev, 
                                                    configuration["degredation"],
                                                    configuration["escalation"],
                                                    configuration["capex_years"])
                tmp["Export [kWh]"] += tmp[var2label[scenario][k]]
                tmp["Revenue [$]"]  += tmp[revenue_label]

            #### COST
            capex = 0
            om = 0
            for k in annual_vars[scenario]["capex"]:
                tmp_capex, tmp_om = calc_capex_and_om(configuration[f"{k}_dollar_per_kw"],
                                                      configuration[f"{k}_om_dollar_per_kw_year"],
                                                      input_config[annual_vars[scenario]["scale"][k]],
                                                      capex_reduce_fraction=configuration.get(f"{k}_inverter_fraction", 0)
                                                      )
                capex += tmp_capex
                om    += tmp_om
            input_config[f"{scenario} CAPEX [$]"] = capex
            input_config[f"{scenario} O&M [$/year]"] = om
            input_config[f"{scenario} Annualized CAPEX [$]"] = annualized_cost(capex,0, configuration["discount_rate"], configuration["escalation"], configuration["capex_years"])
            tmp["Cost [$]"] = annualized_cost(capex, om, configuration["discount_rate"], configuration["escalation"], configuration["capex_years"])
            tmp["Profit [$]"]  = tmp["Revenue [$]"] - tmp["Cost [$]"]

            net_present_value[scenario] = npv(configuration["discount_rate"], tmp["Profit [$]"])
            
            #### Curtailment
            k = annual_vars[scenario]["curtailment"]
            annual_curt = summary_out[scenario][k].loc[:, var2label[scenario][k]].sum(axis=0).squeeze()
            curt_cost = summary_out[scenario][k].loc[:, configuration["energy_price_col"]].sum(axis=0).squeeze() + \
                        summary_out[scenario][k].loc[:, configuration["dvr_price_col"]].sum(axis=0).squeeze() * (configuration["dvr_adjust"] - 1)
            
            tmp["Curtailment [kWh]"] = annual_benefit(annual_curt, configuration["degredation"], 0, configuration["capex_years"]) 
            tmp["Curtailment Opportunity Cost [$]"] = annual_benefit(curt_cost, configuration["degredation"], configuration["escalation"], configuration["capex_years"]) 

            net_present_value[scenario + " Upgrade NPV"] = npv(configuration["discount_rate"], tmp["Curtailment Opportunity Cost [$]"])
            
            #### Save
            yearly_out[scenario] = pd.DataFrame(tmp)
            yearly_out[scenario].to_excel(writer, sheet_name=f"{scenario} Annual")

        pd.Series(net_present_value).to_excel(writer, sheet_name="NPV")
        ### save configuration
        pd.Series(input_config).to_excel(writer, sheet_name="configuration")

    ## plot freshly created results
    if props_to_plot:

        ### just plot, don't run first
        scenarios = ["FIX+BESS", "FIX"]
        if configuration["run_no_fix"]:
            scenarios.append("No FIX")
        for prop in props_to_plot:
            plot_res(yearly_out, scenarios, prop, configuration.get("plot_path", args.plot_path))               
        