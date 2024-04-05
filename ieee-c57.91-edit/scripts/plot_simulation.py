
import transformer_thermal_models as xmdl
from transformer_thermal_models import Transformer, LoadConditions
import pandas as pd
import argparse, warnings, os, io, json
import tempfile

def main(h5path, key, savename):
    
    print("loading data...", end="")
    with pd.HDFStore(h5path, mode="r") as hdf:
        xfrm = Transformer()
        ## load transformer configuration
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as fp:
            xfrmconfig = pd.read_hdf(hdf, "/xfrmconfig").loc["xfrm"].to_dict()
            json.dump(xfrmconfig, fp)
            fp.close()
            xfrm.from_json(fp.name)
            os.remove(fp.name)
        
        tmp = pd.read_hdf(hdf, key=key+"/solution")
        # else: # csv
        #     tmp = pd.read_csv(xfrmsol, parse_dates=[0])
        tmp["Time [Datetime]"] = (tmp["Time [Datetime]"]-tmp["Time [Datetime]"].iloc[0]).apply(lambda x: x.total_seconds()/60.0).values
        tmp.rename(columns={"Time [Datetime]": "Time [Minutes]"}, inplace=True)
        xfrm.solution = tmp
        
        #Load loading conditions file
        lc = LoadConditions()
        load_config = pd.read_hdf(hdf, key=key+"/lc").to_csv(index=False)
        lc.import_data(io.StringIO(load_config))
        print("complete.")

    
    print("plotting...", end="")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        fig, tab = xmdl.plotting.plot_results_plotly(xfrm,lc)
    # from https://stackoverflow.com/questions/59868987/saving-multiple-plots-into-a-single-html
    with open(savename,"w") as f:
        f.write(fig.to_html(include_plotlyjs="cdn"))
        f.write(tab.to_html(full_html=False, include_plotlyjs=False))
    print("complete.")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="transformer thermal modeling simulation")
    parser.add_argument("h5path", help="h5 solution")
    parser.add_argument("key", help="configuration key")
    parser.add_argument("savename", help="save name for figure (html)")
    args = parser.parse_args()
    
    main(args.h5path, args.key, args.savename)