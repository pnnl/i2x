
import transformer_thermal_models as xmdl
from transformer_thermal_models import Transformer, LoadConditions
import pandas as pd
import argparse, warnings, os

def main(xfrm_config, load_config, savename):
    
    print("loading data...", end="")
    #Load transformer data
    xfrm = Transformer()
    xfrm.from_json(xfrm_config)
    tmp = pd.read_csv(savename, parse_dates=[0])
    tmp["Time [Datetime]"] = (tmp["Time [Datetime]"]-tmp["Time [Datetime]"].iloc[0]).apply(lambda x: x.total_seconds()/60.0).values
    tmp.rename(columns={"Time [Datetime]": "Time [Minutes]"}, inplace=True)
    xfrm.solution = tmp
    #Load loading conditions file
    lc = LoadConditions()
    lc.import_data(load_config)
    print("complete.")

    
    print("plotting...", end="")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        fig, tab = xmdl.plotting.plot_results_plotly(xfrm,lc)
    # from https://stackoverflow.com/questions/59868987/saving-multiple-plots-into-a-single-html
    with open(os.path.splitext(savename)[0]+".html","w") as f:
        f.write(fig.to_html(include_plotlyjs="cdn"))
        f.write(tab.to_html(full_html=False, include_plotlyjs=False))
    print("complete.")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="transformer thermal modeling simulation")
    parser.add_argument("xfrmconfig", help="transformer thermal namplate configuration json")
    parser.add_argument("loadconfig", help="Load condition csv data")
    parser.add_argument("savename", help="path with solution to plot")
    args = parser.parse_args()
    
    main(args.xfrmconfig, args.loadconfig, args.savename)