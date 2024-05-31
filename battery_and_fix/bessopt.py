import pyomo.environ as pyo
import numpy as np
import pandas as pd
import argparse, sys, os
import tomli
from i2x.der_hca.hca import print_config

def main(bes_kw:float, bes_kwh:float, f:np.ndarray, hc:np.ndarray,
         savename="bessopt.xlsx", print_model=False, **kwargs):
    model = pyo.ConcreteModel()
    
    hrs = list(range(len(hc)))
    model.n_hrs = len(hrs)
    model.f = f
    model.hc = hc

    ## battery output
    model.bess = pyo.Var(hrs, bounds=(-bes_kw, bes_kw))
    model.E = pyo.Var(hrs, bounds=(0,bes_kwh))

    @model.Constraint(hrs)
    def soc_rule(model, h):
        """battery state of charge change"""
        return model.E[h] == model.E[(h-1) % model.n_hrs] + model.bess[h]

    @model.Constraint(hrs)
    def no_gridcharge_rule(model, h):
        """Power output is >0 (no charging from grid)"""
        return model.bess[h] + model.f[h] >= 0
    
    ## curtailment is forecast minus hosting capacity 
    ## **if** hosting capacity is less than forecast,
    ## otherwise zero
    model.curt = f - np.vstack([f, hc]).min(axis=0)

    @model.Constraint([h for h in hrs if model.curt[h] == 0])
    def output_rule(model, h):
        """bess is not allowed to push output past hc"""
        return model.bess[h] + model.f[h] <= model.hc[h]
    

    @model.Objective(sense=pyo.minimize)
    def obj(model):
        """objective is to maximize charging (minimize negative injection) 
        during hours where curtailment would occur.
        curtailment without BESS is f - min(f, hc), which will be >= 0.
        Hours where curtailment would occur are those where curtailment > 0
        """
        return sum(model.bess[h] for h in hrs if model.curt[h] > 0)

    opt = pyo.SolverFactory("ipopt")
    
    opt.solve(model)
    if print_model:
        model.pprint()
    
    ## form https://stackoverflow.com/questions/67491499/how-to-extract-indexed-variable-information-in-pyomo-model-and-build-pandas-data
    vars = []
    all_vars = model.component_map(ctype=pyo.Var)
    for k,v in all_vars.items():
        vars.append(pd.Series(v.extract_values(), name=k))

    df_vars = pd.concat(vars, axis=1)

    output = (df_vars["bess"] + f).rename("output")
    curt = (output - np.vstack([output, hc]).min(axis=0)).rename("curtailment")
    output -= curt
    ## add output 
    df_vars = pd.concat([df_vars, output, curt], axis=1)

    df_fixed = pd.DataFrame({"forecast": f, "HC": hc})
    with pd.ExcelWriter(savename) as writer:
        df_fixed.to_excel(writer, sheet_name="fixed")
        df_vars.to_excel(writer, sheet_name="variables")

       

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



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find profiles nearest to desired points")
    parser.add_argument("configfile", help=".toml configuration")
    parser.add_argument("--print-hca-stats", help="print hca statistics and exit.", action="store_true")
    args = parser.parse_args()
    # bes_kw  = 200
    # bes_kwh = 400
    # hc = np.array([1000, 700, 700, 1350.5, 1200.0])
    # f  = np.array([500, 800.0, 1000.0, 850.0, 600.2])
    
    with open(args.configfile, mode='rb') as f:
        configuration = tomli.load(f)
    print_config(configuration, printtype=True)
    for k in ["hc", "f"]:
        if isinstance(configuration[k], str):
            configuration[k] = load_data_profile(configuration[k], configuration[f"{k}_col"], 
                                configuration.get(f"{k}_sheet_name", None),
                                configuration.get(f"{k}_index_col", 0))
        else:
            configuration[k] = np.array(configuration[k])
    ## apply scaling
    configuration["f"] *= configuration["fscale"]
    print_config(configuration, title="Post Convert Configuration", printtype=True)
    if args.print_hca_stats:
        profile_stats(configuration["hc"], name="HC ")
        profile_stats(configuration["f"], name="PV profile ")
        sys.exit(0)
    
    main(**configuration)