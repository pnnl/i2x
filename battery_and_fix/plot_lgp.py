import pandas as pd
pd.options.plotting.backend = "plotly"
import plotly.io as pio
from bessopt import save_plot
import argparse

pd.options.plotting.backend = "plotly"
pio.templates.default = "plotly_white"

PLOTLY_LAYOUT = {"font_size": 20, "font_family":"Arial", 
                 "width":800, "height":600,
                 "legend": dict(x=0.5, y=1, xanchor="center", yanchor="bottom", orientation="h")}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve for optimal BESS utilization given solar profile and hosting capacity results")
    parser.add_argument("lgpfile", help=".csv with lgp curves")
    parser.add_argument("--save", help="path to save, if empty, plot will not save", default="")
    args = parser.parse_args()
    df = pd.read_csv(args.lgpfile, index_col=0)
    fig = df.plot(labels={"index":"Time", "value":"HC [kW]", "variable": "LGP"})
    fig.update_layout(**PLOTLY_LAYOUT)
    
    if args.save:
        save_plot(fig, "archive/lgp")

        fig = df.loc["2024-03-20":"2024-04-10"].plot(labels={"index":"Time", "value":"HC [kW]", "variable": "LGP"})
        fig.update_layout(**PLOTLY_LAYOUT)
        save_plot(fig, "archive/lgp_zoom")
    else:
        fig.show()