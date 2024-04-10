
import pandas as pd
import transformer_thermal_models as xmdl
from transformer_thermal_models import Transformer, LoadConditions
import argparse, sys, os, io
import tomli, json
import itertools
import numpy as np

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

def mk_data_avg_min(event_time, pnom:float, pover:float, 
            t_amb:float=30):
    
    if event_time < 60:
        ## normalize to average minute load
        ## based on equation (5) of C5791-2011 section 7.1.2
        ## Leq = [(L1^2*t1 + ... + LN^2t_n)/(t1 + ... + tN)]^0.5
        
        pover = np.sqrt(np.power(pover,2)*event_time + np.power(pnom,2)*(60-event_time))/np.sqrt(60)
        event_time = 60
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

def mk_data_ramp(event_time, pnom:float, pover:float, 
            t_amb:float=30):
    
    # deltap = pover - pnom
    # max_deltap = 0.05 # max delta p per sec calculated from 3p.u/60 sec
    start_time = "2024-01-02 12:00"
    ramp = np.logspace(np.log10(pnom), np.log10(pover), 6).tolist()
    tramp = [pd.to_datetime(start_time) - n*pd.Timedelta(seconds=1) for n in np.linspace(1,0,6)]
    out = {"Time": [pd.to_datetime(start_time) - pd.Timedelta(hours=12), 
                    pd.to_datetime(start_time) - pd.Timedelta(minutes=5)] + 
                    tramp +
                    [pd.to_datetime(start_time) + pd.Timedelta(seconds=event_time),
                    pd.to_datetime(start_time) + pd.Timedelta(hours=6),
                    pd.to_datetime(start_time) + pd.Timedelta(hours=12)],
           "Ambient": [t_amb]*11,
           "Load":[pnom, pnom] + ramp + [pnom, pnom, pnom],
           "Plot": [False, True] + [True]*6 + [True, False, False]
    }

    return pd.DataFrame(out)

def main(xfrm_config, load_config, ret=True,
         savename="",
         method="main_clause_7_diff", integration_method="RK45",
         output_res = "sec", mk_data_method="min_normalize"):
    
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
    xmdl.solve_temperatures(xfrm, lc, method, integration_method=integration_method)
    xmdl.solve_estimated_loss_of_life(xfrm, lc)
    print("complete.")

    print(f"\texporting data...", end="")
    output = xmdl.export_data(xfrm, lc, res=output_res, output_pandas=True)
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
    if "method" not in config:
        config["method"] = args.method
    if not config["loadconfig"]:
        for k in ["pnom", "pover", "event_time"]:
            if not isinstance(config[k], list):
                config[k] = [config[k]]
    print_inputs(config)
    mk_data_method = config.get("mk_data_method", "min_normalize")
    if not config["loadconfig"]:
        with pd.HDFStore(os.path.join(config["results_path"], "res.h5"), mode="w", complevel=1) as hdf:
            ## store transformer configuration
            with open(config["xfrmconfig"]) as f:
                pd.DataFrame(json.load(f), index=["xfrm"]).to_hdf(hdf, key="/xfrmconfig")
            pd.DataFrame.from_dict(config, orient="index", columns=["input_config"]).to_hdf(hdf, key="/input_config")
            for pnom, pover, event_time in itertools.product(config["pnom"], config["pover"], config["event_time"]):
                print(f"pnom {pnom} | pover {pover} | event_time {event_time}")
                filename = f"ln{round(pnom*100)}_lv{round(pover*100)}_tv{event_time}.csv"
                config_results = os.path.join(config["results_path"], "load_configs")
                if mk_data_method == "direct":
                    lc = mk_data(event_time, pnom, pover)
                elif mk_data_method == "min_normalize":
                    lc = mk_data_avg_min(event_time, pnom, pover)
                elif mk_data_method == "ramp":
                    lc = mk_data_ramp(event_time, pnom, pover)
                else:
                    raise ValueError("mk_data_method must be one of 'direct', 'min_normalize', 'ramp'.")
                
                ### save configuration
                if not os.path.exists(config_results):
                    os.mkdir(config_results)
                lc.to_csv(os.path.join(config_results, filename), index=False)
                
                sim_results = os.path.join(config["results_path"], "results")

                res = main(config["xfrmconfig"], io.StringIO(lc.to_csv(index=False)), ret=True,
                           method=config["method"], 
                           integration_method=config.get("integration_method", "RK45"),
                           output_res=config.get("output_res", "sec"))
                key = f"/ln{round(pnom*100)}/lv{round(pover*100)}/tv{event_time}"
                res.to_hdf(hdf, key=key+"/solution")
                lc.to_hdf(hdf, key=key+"/lc")

    sys.exit(0)
    main(args.xfrmconfig, args.loadconfig, args.savename, args.method)