from helper.helper_methods import read_input, write_output, get_centroids
from queued_up.initial_output import cleanup, init_output
from queued_up.solar_wind import final_output
from pathlib import Path

QUEUED = 'queues'
QUEUED_SHEET = 'data'
SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
PARENT_DIR = SCRIPT_DIR.parent # Get the parent directory
OUTPUT_DIR = PARENT_DIR / 'hubdata' / 'output' / 'queued_up.csv'# Get the output directory

def qu_driver():
    centroids = get_centroids()
    # print("centroids: ",centroids)
    input_df = read_input(QUEUED, QUEUED_SHEET)
    # print("data_df: ", data_df)
    clean_df = cleanup(input_df)
    # print("clean_df: ", data_df)
    initial_df = init_output(clean_df)
    # print("initial_df: ", initial_df)
    final_df = final_output(clean_df, initial_df)
    result = final_df.merge(centroids,  how = 'inner', on = ['state_county'])
    
    write_output(result, OUTPUT_DIR)


