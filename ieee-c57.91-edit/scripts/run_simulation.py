
import pandas as pd
import transformer_thermal_models as xmdl
from transformer_thermal_models import Transformer, LoadConditions
import argparse, sys, os, io
import tomli, json
import itertools

def load_config(filepath, default_path=None):
    
    if default_path is not None:
        with open(default_path, mode='rb') as f:
            inputs = tomli.load(f)
    else:
        inputs = {}
    
    if filepath:
        with open(filepath, mode='rb') as f:
            user = tomli.load(f)
    else:
        user = {}

    for k, v in user.items():
        inputs[k] = v
    
    return inputs

def print_inputs(args, logger=None):
    """ print command line inputs and data type"""
    if logger is not None:
        print = logger.info
    else:
        import builtins
        print = builtins.print
    print("Inputs:\n==============")
    if type(args) != dict:
        for k, v in vars(args).items():
            print(f'{k} : {v} type: {type(v)}') 
    else:
        for k, v in args.items():
            print(f'{k} : {v} type: {type(v)}') 

def mk_data(event_time, pnom:float, pover:float, 
            t_amb:float=30):
    
    start_time = "2024-01-02 12:00"
    out = {"Time": [pd.to_datetime(start_time) - pd.Timedelta(hours=12), 
                    pd.to_datetime(start_time) - pd.Timedelta(minutes=5), 
                    pd.to_datetime(start_time),
                    pd.to_datetime(start_time) + pd.Timedelta(seconds=event_time),
                    pd.to_datetime(start_time) + pd.Timedelta(hours=6),
                    pd.to_datetime(start_time) + pd.Timedelta(hours=12)],
           "Ambient": [t_amb]*6,
           "Load":[pnom, pnom, pover, pnom, pnom, pnom],
           "Plot": [False, True, True, True, False, False]
    }

    return pd.DataFrame(out)

def main(xfrm_config, load_config, ret=True,
         savename="",
         method="main_clause_7_diff"):
    
    print("\tloading data...", end="")
    #Load transformer data
    xfrm = Transformer()
    xfrm.from_json(xfrm_config)

    #Load loading conditions file
    lc = LoadConditions()
    lc.import_data(load_config)
    print("complete.")

    ## solve temperatures
    print("\tsolving model...", end="")
    xmdl.solve_temperatures(xfrm, lc, method)
    xmdl.solve_estimated_loss_of_life(xfrm, lc)
    print("complete.")

    print(f"\texporting data...", end="")
    output = xmdl.export_data(xfrm, lc, sec_res=True, output_pandas=True)
    ## fixed headers
    # output.rename(columns=lambda x: x.replace(" ","_").replace("[","").replace("]","").replace(".","").lower(), inplace=True)
    print("complete.")
    if savename:
        output.to_csv(savename, index=False)
    if ret:
        return output
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="transformer thermal modeling simulation")
    parser.add_argument("config", help="configuration toml file")
    # parser.add_argument("xfrmconfig", help="transformer thermal namplate configuration json")
    # parser.add_argument("loadconfig", help="Load condition csv data")
    # parser.add_argument("savename", help="path to save csv output")
    parser.add_argument("--method", choices=xmdl.AVAILABLE_METHODS.keys(), help="solution method", default="main_clause_7_diff")
    args = parser.parse_args()
    
    config = load_config(args.config)
    config["method"] = args.method
    if not config["loadconfig"]:
        for k in ["pnom", "pover", "event_time"]:
            if not isinstance(config[k], list):
                config[k] = [config[k]]
    print_inputs(config)
    if not config["loadconfig"]:
        with pd.HDFStore(os.path.join(config["results_path"], "res.h5"), mode="w", complevel=1) as hdf:
            ## store transformer configuration
            with open(config["xfrmconfig"]) as f:
                pd.DataFrame(json.load(f), index=["xfrm"]).to_hdf(hdf, key="/xfrmconfig")
            for pnom, pover, event_time in itertools.product(config["pnom"], config["pover"], config["event_time"]):
                print(f"pnom {pnom} | pover {pover} | event_time {event_time}")
                filename = f"ln{round(pnom*100)}_lv{round(pover*100)}_tv{event_time}.csv"
                config_results = os.path.join(config["results_path"], "load_configs")
                lc = mk_data(event_time, pnom, pover)
                
                ### save configuration
                if not os.path.exists(config_results):
                    os.mkdir(config_results)
                lc.to_csv(os.path.join(config_results, filename), index=False)
                
                sim_results = os.path.join(config["results_path"], "results")

                res = main(config["xfrmconfig"], io.StringIO(lc.to_csv(index=False)), ret=True)
                key = f"/ln{round(pnom*100)}/lv{round(pover*100)}/tv{event_time}"
                res.to_hdf(hdf, key=key+"/solution")
                lc.to_hdf(hdf, key=key+"/lc")

    sys.exit(0)
    main(args.xfrmconfig, args.loadconfig, args.savename, args.method)