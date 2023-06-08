from helper.read_input import read_input
import pandas as pd

SOLARTRACE = 'SolarTRACE'
SOLARTRACE_SHEET = 'AHJ Utility Combinations'

def st_driver():
    ahj_utility_df = read_input(SOLARTRACE, SOLARTRACE_SHEET, 2, 0)
    if ahj_utility_df is None:
        print('File Not found in directory.')
    print("ahj_utility_df: ", ahj_utility_df)