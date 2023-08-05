import pandas as pd
from pathlib import Path
import requests, json

pd.options.mode.chained_assignment = None  # default='warn'

RESERVATION_COLS = ["GEOID","BASENAME","NAME","Lat","Lon"]
COUNTY_COLS = ["POPULATION", "POP_SQMI", "SQMI", "ORIG_FID"]

# Define the components of the file path
SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
PARENT_DIR = SCRIPT_DIR.parent.parent # Get the parent directory
INPUT_DIR = PARENT_DIR / 'hubdata' / 'input' # Get the input directory
INPUT_FILE = 'CENTROIDS' # Choose the input file that contains centroids (keep this uppercase for consistency)
API_STRING = 'https://nominatim.openstreetmap.org/search?format=json'


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
    selected_cenrtroids = centroids_county_geoid[['STATE_NAME', 'STATE_ABBR', 'state_county', 'lat', 'lon']]
    #
    selected_cenrtroids['state_county'] = selected_cenrtroids['state_county'].astype('string') # Change the type from object to string to use the string class.
    return selected_cenrtroids

# # Define the components of the file path
# SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
# PARENT_DIR = SCRIPT_DIR.parent.parent # Get the parent directory
# INPUT_DIR = PARENT_DIR / 'hubdata' / 'input' # Get the input directory

def read_input(input_str, sheet, header=None, index_col=None):
    # centroids_reservations = pd.read_csv('AIANNHA_centroids.csv')[COLS]
    all_files = list(INPUT_DIR.glob('*'))
    for file in all_files: # Loop over all files
        if input_str in file.name: # Check if 'SolarTRACE' is in the file name
            xlsx = pd.ExcelFile(file)
            df = pd.read_excel(xlsx, sheet, header=header, index_col=index_col)
            if header is None and index_col is None:
                df = pd.read_excel(xlsx, sheet)
            return df
    return None

def add_state_full(df):
    temp_df = df.copy()
    centroids = get_centroids()
    state_dict = centroids.set_index('STATE_ABBR')['STATE_NAME'].to_dict()
    temp_df.insert(1, 'state_full', df['state'].map(state_dict))
    return temp_df

def get_api_result(row):
    try:
        if row.get('ahj') is None:
            return pd.Series([None, None])
        print(row['ahj'])
        row_state = row[0]
        row_ahj = row[1].split()[:-1]
        response = requests.get(f'{API_STRING}&state={row_state}&city={row_ahj}')
        data = response.json()
        if data and len(data) >= 1:
            result = pd.Series([data[0]['lat'], data[0]['lon']])
            print("THE SEIRES: ", result)
            return result
        else:
            return pd.Series([None, None])  # Default values

    except json.JSONDecodeError:  # Catch the exception
        return pd.Series([None, None])  # Return default values

def write_output(df, output_dir):
    df.fillna(0.0).to_csv(output_dir, index=False)
