import pandas as pd
from helper.helper_methods import get_api_result


def api_call(df):
    '''
    This function calls the NOMINATIM API and loops through all the rows of solar trace data finding lat lon for each row.
    '''
    df_temp = df.copy()
    df_temp[['lat', 'lon']] = df[['state_full', 'ahj']].apply(get_api_result, axis=1)
    return df_temp


def final_processing(api_df,weighted_df):
    '''
    This function concatenates the api results from the previous module on this file with the rest of the results from the main_processing, 
    adding the lat lons to create a final df for the output file.
    '''
    result = pd.concat([api_df.iloc[:, list(range(6)) + list(range(-22, 0))], weighted_df.iloc[:,-10:]],axis=1).drop('geo_id', axis=1).reset_index()
    return result