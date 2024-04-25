import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def main(start_time:str, end_time:str, 
         start_tevent:str, end_tevent:str,
         pnom:float, pover:float, 
         export_tmin:int=2, export_tmax:int=30, rest_tmin:int=2, rest_tmax:int=10, 
         t_amb:float=30,
         seed=None):
    
    random_state = np.random.RandomState(seed)
    
    out = {"Time": [pd.to_datetime(start_time), pd.to_datetime(start_tevent) - pd.Timedelta(minutes=1), pd.to_datetime(start_tevent)],
           "Ambient": [t_amb, t_amb, t_amb],
           "Load":[pnom, pnom, pover],
           "Plot": [False, True, True]
    }

    while out["Time"][-1] < pd.Timestamp(end_tevent):
        ## export event
        out["Time"].append(out["Time"][-1] + pd.Timedelta(seconds=random_state.randint(export_tmin, export_tmax)))
        out["Ambient"].append(t_amb)
        out["Load"].append(pnom)
        out["Plot"].append(True)

        ## rest
        out["Time"].append(out["Time"][-1] + pd.Timedelta(minutes=random_state.randint(rest_tmin, rest_tmax)))
        out["Ambient"].append(t_amb)
        out["Load"].append(pover)
        out["Plot"].append(True)
    
    ## last event
    out["Time"].append(out["Time"][-1] + pd.Timedelta(seconds=random_state.randint(export_tmin, export_tmax)))
    out["Ambient"].append(t_amb)
    out["Load"].append(pnom)
    out["Plot"].append(True)
    
    ## end of plot window
    out["Time"].append(out["Time"][-1] + pd.Timedelta(hours=1))
    out["Ambient"].append(t_amb)
    out["Load"].append(pnom)
    out["Plot"].append(False)

    out["Time"].append(pd.to_datetime(end_time))
    out["Ambient"].append(t_amb)
    out["Load"].append(pnom)
    out["Plot"].append(False)

    return pd.DataFrame(out)

if __name__ == '__main__':
    pass
