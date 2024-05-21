import pyomo.environ as pyo
import numpy as np
import pandas as pd

def main(bes_kw:float, bes_kwh:float, f:np.ndarray, hc:np.ndarray,
         savename="bessopt.xlsx"):
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

    
    

    

   

    



if __name__ == "__main__":
    bes_kw  = 200
    bes_kwh = 400
    hc = np.array([1000, 700, 700, 1350.5, 1200.0])
    f  = np.array([500, 800.0, 1000.0, 850.0, 600.2])
    main(bes_kw, bes_kwh, f, hc)