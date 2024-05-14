"""add winding column to all the regulator shapes exported
from a year run with the 9500 feeder
"""
import pandas as pd
import os

if __name__ == "__main__":
    d = "regulator_taps"
    for f in os.listdir("regulator_taps"):
        p = os.path.join(d, f)
        df = pd.read_csv(p).iloc[:,:3]
        df = df.assign(wdg=2)
        df.columns = ["hr", "sec", "tap_pu", "wdg"]
        psave = os.path.splitext(p)[0] + "wdg.csv"
        df.loc[:, ["hr", "sec", "wdg", "tap_pu"]].to_csv(psave, index=False)