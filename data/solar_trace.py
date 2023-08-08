import pandas as pd
from pathlib import Path
from helper.helper_methods import read_input, get_centroids, write_output, add_state_full
from solarTRACE.initial_processing import rename_cols, aggregate
from solarTRACE.main_processing import total, weighted_pre, full
from solarTRACE.final_processing import api_call, final_processing
import pickle, time

SOLARTRACE = 'SolarTRACE'
SOLARTRACE_SHEET = 'AHJ Utility Combinations'
pd.options.mode.chained_assignment = None  # default='warn'
pd.set_option('display.float_format', '{:.2f}'.format)
SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
PARENT_DIR = SCRIPT_DIR.parent # Get the parent directory
OUTPUT_DIR = PARENT_DIR / 'hubdata' / 'output' / 'solarTRACE.csv'# Get the output directory

def st_driver():
    ahj_utility_df = read_input(SOLARTRACE, SOLARTRACE_SHEET, 2, 0)
    # print("ahj_utility_df: ", ahj_utility_df)
    if ahj_utility_df is None:
        print('File Not found in directory.')
    renamed_df = rename_cols(ahj_utility_df)
    # print("renamed_df: ", renamed_df)
    agg_df = aggregate(renamed_df)
    # print('agg_df ', agg_df)
    total_df = total(agg_df)
    #
    weighted_df = weighted_pre(total_df)
    full_df = full(weighted_df, total_df)
    full_df = add_state_full(full_df)
    # print('full_df ', full_df)
    # start = time.time()
    api_df = api_call(full_df)
    # end = time.time()
    # print('API CALL TIME: ',end-start)
    final_df = final_processing(api_df,weighted_df)
    
    #TESTING CODE
    # Writing to a file
    # with open('result.pkl', 'wb') as file:
    #     pickle.dump(final_df, file)
    # Reading from a file
    # with open('result.pkl', 'rb') as file:
    #     loaded_result = pickle.load(file)
    # write_output(loaded_result, OUTPUT_DIR)
    # print(loaded_result['lat'])
    
    write_output(final_df, OUTPUT_DIR)
    