import pandas as pd
from helper.helper_methods import get_api_result

def api_call(df):
    df_temp = df.copy()
    df_temp[['lat', 'lon']] = df[['state_full', 'ahj']].apply(get_api_result, axis=1)
    return df_temp

def final_processing(api_df,weighted_df):
    result = pd.concat([api_df.iloc[:, list(range(6)) + list(range(-22, 0))], weighted_df.iloc[:,-10:]],axis=1).drop('geo_id', axis=1).reset_index()
    return result