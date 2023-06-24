import pandas as pd
from helper.read_input import read_input

SOLARTRACE = 'SolarTRACE'
SOLARTRACE_SHEET = 'AHJ Utility Combinations'

def st_driver():
    ahj_utility_df = read_input(SOLARTRACE, SOLARTRACE_SHEET, 2, 0)
    # print("ahj_utility_df: ", ahj_utility_df)
    if ahj_utility_df is None:
        print('File Not found in directory.')
    # clean_df = cleanup(ahj_utility_df)
    # print("clean_df: ", clean_df)

def cleanup(df):
    
    # Convert "q_date" column to date/time format (NOTE: There is no time section)
    df['q_date'] = pd.to_datetime(df['q_date'], errors='coerce')
    # Remove the empty rows. There are 687 nulls in the "q_date" column --> 24381-23694=687
    df = df[~df.q_date.isnull()].reset_index().tail()
    # Convert "on_date" column to date/time format (NOTE: Only 1571 entries have on_date)
    df['on_date'] = pd.to_datetime(df['on_date'], errors='coerce')
    df = df[~df.on_date.isnull()].reset_index()
    return df