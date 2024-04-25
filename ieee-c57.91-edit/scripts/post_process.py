import pandas as pd
import re
import transformer_thermal_models as xmdl
import argparse, sys, os


def main(h5path, hssettle=1.05):
    with pd.HDFStore(h5path, mode='r+', complevel=1) as hdf:
        xfrmconfig = pd.read_hdf(hdf, key="/xfrmconfig").loc["xfrm"].to_dict()
        
        # rated hotspot
        T_hsr = xfrmconfig["T_hsr"]+xfrmconfig["T_ambr"]
        
        out = {}
        for key in hdf.keys():
            if "solution" not in key:
                continue
            
            print(f"working on key {key}...")
            ln, lv, tv = map(int, re.findall(r'\d+', key))
            
            ## get solution
            sol = pd.read_hdf(hdf, key=key)

            ## get event
            ldvals = sol["Load [1]"].drop_duplicates().values
            if ldvals.shape[0] != 2:
                raise ValueError(f"Expecting exactly 2 unique load values, got {ldvals}.")
            tmp = sol.loc[lambda x: x["Load [1]"] == ldvals[1]]

            ## get second before event (initial hot spot)
            # idx0 = tmp.index[0] - 1
            # hs0 = sol.loc[idx0, "Hot Spot [C]"]

            ## initial hot spot is average over hour before event
            idx0 = tmp.index[0]
            t0 = tmp.loc[idx0, "Time [Datetime]"]
            td = pd.Timedelta(1, "h")
            hs0 = sol.loc[lambda x: (x["Time [Datetime]"] >= (t0 - td)) & (x["Time [Datetime]"] < t0), "Hot Spot [C]"].mean()
            
            ## get time where temperature has settled and settling time (seconds)
            idxf = sol.loc[lambda x: (x.index >= tmp.index[-1]) & (x["Hot Spot [C]"] <= hssettle*hs0)].index[0]
            ts = (sol.loc[idxf, "Time [Datetime]"] - t0).seconds #record time from event start to settling

            ## calculate equivalent aging
            A = xmdl.constants.ageing_A.get(xfrmconfig["liquid_type"].lower(),9.8E-18)
            B = xmdl.constants.ageing_B.get(xfrmconfig["liquid_type"].lower(),15000.)
            tminutes = (sol.loc[idx0:idxf, "Time [Datetime]"] - sol.loc[idx0, "Time [Datetime]"]).apply(lambda x: x.total_seconds()/60).values
            per_unit_life, faa, feqa, loss_of_life = xmdl.estimate_loss_of_life(
                sol.loc[idx0:idxf, "Hot Spot [C]"].values,
                tminutes,
                T_reference=T_hsr,
                TUK = xfrmconfig["TUK"],
                A = A, B = B, nominal_insulation_life=180000
            )

            ## since FEQA is cummulative, we store the last value
            out[(ln, lv, tv)] = {"ts": ts, "feqa": feqa[-1], 
                                 "hs0": hs0, "hspeak":sol.loc[idx0:idxf, "Hot Spot [C]"].max(),
                                 "hsf": sol.loc[idxf, "Hot Spot [C]"]}
            print("complete.")
        
        ## write solution to hdf
        out = pd.DataFrame.from_dict(out, orient="index").rename_axis(["ln", "lv", "tv"])
        out.to_hdf(hdf, key="/post_process/analysis")

        ## save configuration
        pd.DataFrame.from_dict({"hssettle": hssettle}, orient="index", columns=["value"]).to_hdf(hdf, key="/post_process/config")

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="post process thermal simulation")
    parser.add_argument("h5path", help="path to h5 to post process")
    parser.add_argument("--hssettle", type=float, help="factor of initial hot spot temperature that counts as settled (default=1.05)", default=1.05)
    args = parser.parse_args()

    main(args.h5path, args.hssettle)