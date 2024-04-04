
import transformer_thermal_models as xmdl
from transformer_thermal_models import Transformer, LoadConditions
import argparse

def main(xfrm_config, load_config, savename,
         method="main_clause_7_diff"):
    
    print("loading data...", end="")
    #Load transformer data
    xfrm = Transformer()
    xfrm.from_json(xfrm_config)

    #Load loading conditions file
    lc = LoadConditions()
    lc.import_data(load_config)
    print("complete.")

    ## solve temperatures
    print("solving model...", end="")
    xmdl.solve_temperatures(xfrm, lc, method)
    xmdl.solve_estimated_loss_of_life(xfrm, lc)
    print("complete.")

    print(f"saving data to {savename}...", end="")
    output = xmdl.export_data(xfrm, lc, sec_res=True, output_pandas=True)
    output.to_csv(savename, index=False)
    print("complete.")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="transformer thermal modeling simulation")
    parser.add_argument("xfrmconfig", help="transformer thermal namplate configuration json")
    parser.add_argument("loadconfig", help="Load condition csv data")
    parser.add_argument("savename", help="path to save csv output")
    parser.add_argument("--method", choices=xmdl.AVAILABLE_METHODS.keys(), help="solution method", default="main_clause_7_diff")
    args = parser.parse_args()
    
    main(args.xfrmconfig, args.loadconfig, args.savename, args.method)