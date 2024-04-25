
import transformer_thermal_models as xmdl
from transformer_thermal_models import Transformer, LoadConditions
import pandas as pd
import argparse, warnings, os, io, json, sys
import tempfile, textwrap

def main(h5path, key, savename, xlim=None):
    
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
        fig.update_layout(title="<br>".join(textwrap.wrap(os.path.abspath(h5path),width=80)) + "<br>" + key)
        if xlim is not None:
            fig.update_xaxes(range=xlim)
    if savename:
        ext = os.path.splitext(savename)[1]
        if ext == "html":
            # from https://stackoverflow.com/questions/59868987/saving-multiple-plots-into-a-single-html
            with open(savename,"w") as f:
                f.write(fig.to_html(include_plotlyjs="cdn"))
                f.write(tab.to_html(full_html=False, include_plotlyjs=False))
        else:
            fig.update_layout(height=800, width=800)
            fig.write_image(savename)
    else:
        fig.show()
    print("complete.")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="transformer thermal modeling simulation")
    parser.add_argument("h5path", help="h5 solution")
    parser.add_argument("key", help="configuration key")
    parser.add_argument("--savename", help="save name for figure (html, png, pdf, svg)", default="")
    parser.add_argument("--xlim", nargs=2, help="x-axis limits for plot", default=None)
    args = parser.parse_args()
    
    # print(args)
    # sys.exit(0)
    main(args.h5path, args.key, args.savename, args.xlim)