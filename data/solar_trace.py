import pandas as pd
from pathlib import Path
from helper.helper_methods import read_input, get_centroids, write_output, add_state_full
from solarTRACE.initial_processing import rename_cols, aggregate
from solarTRACE.main_processing import total, weighted_pre, full
from solarTRACE.final_processing import api_call, final_processing
import pickle, time

SOLARTRACE = 'SolarTRACE'
SOLARTRACE_SHEET = 'AHJ Utility Combinations'
SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
PARENT_DIR = SCRIPT_DIR.parent # Get the parent directory
OUTPUT_DIR = PARENT_DIR / 'hubdata' / 'output' / 'solarTRACE.csv'# Get the output directory

pd.options.mode.chained_assignment = None  # default='warn'
pd.set_option('display.float_format', '{:.2f}'.format)


def st_driver(bProgress=True):
    '''
    SolarTrace module Driver
    '''
    # For now, we are only reading the AHJ Utility Combinations sheet from the solarTRACE xlsx file
    if bProgress:
        print ('solarTRACE module processing...')
        print ('  Reading input...')
    ahj_utility_df = read_input(SOLARTRACE, SOLARTRACE_SHEET, 2, 0)

    if ahj_utility_df is None:
        print('File Not found in directory.')
    # Combines the 3 first rows of the solarTRACE file that contains column names and returns a df with new col names
    if bProgress:
        print ('  Renaming columns...')
    renamed_df = rename_cols(ahj_utility_df)
    # Group results based on Geo_IDs. We decided geo_id is the best column for this grouping
    if bProgress:
        print ('  Aggregating to GEO ids...')
    agg_df = aggregate(renamed_df)
    # Calculates Totals per discussions
    if bProgress:
        print ('  Totaling PV and storage...')
    total_df = total(agg_df)
    # Weights the pre IX columns per discussions
    if bProgress:
        print ('  Weighting pre-interconnection columns...')
    weighted_df = weighted_pre(total_df)
    # Calculates the full IX columns
    if bProgress:
        print ('  Calculating full interconnection columns...')
    full_df = full(weighted_df, total_df)
    # Adds full state names from the centroids csv file results for API calls based 
    if bProgress:
        print ('  Adding full state names...')
    full_df = add_state_full(full_df)
    # Calls the NOMINATIM API to get all the lat lon results for each geo_id in order for them to be used in the viewer
    if bProgress:
        print ('  API call for locations...')
    api_df = api_call(full_df, bProgress)
    # Combines the API call results and the weighted results from the total_df, weighted_df and full_df to create the final output df
    if bProgress:
        print ('  Final processing...')
    final_df = final_processing(api_df,weighted_df)
    
    
    ''' 
    TESTING CODE: This section can be used to save the results in a pickle file for easier development of the script
    especially the final_processing function instead of waining for the API to fully run the rows through solarTRACE data.
    '''
    # Writing to a file
    # with open('result.pkl', 'wb') as file:
    #     pickle.dump(final_df, file)
    # Reading from a file
    # with open('result.pkl', 'rb') as file:
    #     loaded_result = pickle.load(file)
    # write_output(loaded_result, OUTPUT_DIR)
    # print(loaded_result['lat'])
    
    # writes the final output df to the csv output.
    if bProgress:
        print ('  Writing output...')
    write_output(final_df, OUTPUT_DIR)
    