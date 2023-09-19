from helper.helper_methods import read_input, write_output, get_centroids
from queued_up.initial_output import cleanup, init_output
from queued_up.solar_wind import final_output
from pathlib import Path

QUEUED = 'queues'
QUEUED_SHEET = 'data'
SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
PARENT_DIR = SCRIPT_DIR.parent # Get the parent directory
OUTPUT_DIR = PARENT_DIR / 'hubdata' / 'output' / 'queued_up.csv'# Get the output directory



def qu_driver(bProgress=False):
    '''
    Queued Up module Driver
    '''
    # This function reads the US_county_centroids.csv containing lat lons for counties
    if bProgress:
        print ('Queued-Up module processing...')
        print ('  Getting centroids...')
    centroids = get_centroids()
    # Opens the file and reads from the input file
    if bProgress:
        print ('  Reading input...')
    input_df = read_input(QUEUED, QUEUED_SHEET)
    # Initial cleanup
    if bProgress:
        print ('  Cleaning up...')
    clean_df = cleanup(input_df)
    # 
    if bProgress:
        print ('  Initializing output...')
    initial_df = init_output(clean_df)
    # 
    if bProgress:
        print ('  Finalizing output...')
    final_df = final_output(clean_df, initial_df)
    #
    if bProgress:
        print ('  Merging output...')
    result = final_df.merge(centroids,  how = 'inner', on = ['state_county'])
    
    if bProgress:
        print ('  Writing output...')
    write_output(result, OUTPUT_DIR)


