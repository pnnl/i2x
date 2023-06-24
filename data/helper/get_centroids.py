import pandas as pd
from pathlib import Path
pd.options.mode.chained_assignment = None  # default='warn'

RESERVATION_COLS = ["GEOID","BASENAME","NAME","Lat","Lon"]
COUNTY_COLS = ["POPULATION", "POP_SQMI", "SQMI", "ORIG_FID"]

# Define the components of the file path
SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
PARENT_DIR = SCRIPT_DIR.parent.parent # Get the parent directory
INPUT_DIR = PARENT_DIR / 'hubdata' / 'input' # Get the input directory
INPUT_FILE = 'CENTROIDS' # Choose the input file that contains centroids (keep this uppercase for consistency)

def get_centroids():
    # centroids_reservations = pd.read_csv('AIANNHA_centroids.csv')[COLS]
    all_files = list(INPUT_DIR.glob('*'))
    for file in all_files: # Loop over all files
        if INPUT_FILE in file.name.upper(): # Check if 'centroids' is in the file name
            centroids_county = pd.read_csv(file).drop(COUNTY_COLS, axis=1)
    # attach state and county columns to for the 'state_county' column
    centroids_county_geoid = centroids_county.rename(columns={"FIPS": "geo_id"})
    #
    centroids_county_geoid['NAME'] = centroids_county_geoid['NAME'].apply(lambda x: x.split(' ')[0].lower())
    #
    centroids_county_geoid['state_county'] = centroids_county_geoid.STATE_ABBR.str.cat(centroids_county_geoid.NAME, sep='_')
    #
    selected_cenrtroids = centroids_county_geoid[['state_county', 'lat', 'lon']]
    #
    selected_cenrtroids['state_county'] = selected_cenrtroids['state_county'].astype('string') # Change the type from object to string to use the string class.
    return selected_cenrtroids