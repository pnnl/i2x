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
API_STRING = 'https://nominatim.openstreetmap.org/search?format=json' # Current NOMINATIM URL


def get_centroids():
    '''
    This function is used to interpret and extract infromation from county centroids file that has lat lon for counties.
    It is directly used in the queued up data processing (queues_2021_clean_data.xlsx) and indirectly
    in solarTRACE by converting state abbreviations to state names and geo_ids
    '''
    all_files = list(INPUT_DIR.glob('*'))
    for file in all_files: # Loop over all files
        if INPUT_FILE in file.name.upper(): # Check if 'centroids' is in the file name
            centroids_county = pd.read_csv(file).drop(COUNTY_COLS, axis=1)
    # attach state and county columns to for the 'state_county' column
    centroids_county_geoid = centroids_county.rename(columns={"FIPS": "geo_id"})
    centroids_county_geoid['NAME'] = centroids_county_geoid['NAME'].apply(lambda x: x.split(' ')[0].lower())
    centroids_county_geoid['state_county'] = centroids_county_geoid.STATE_ABBR.str.cat(centroids_county_geoid.NAME, sep='_')
    selected_centroids = centroids_county_geoid[['STATE_NAME', 'STATE_ABBR', 'state_county', 'lat', 'lon']]
    selected_centroids['state_county'] = selected_centroids['state_county'].astype('string') # Change the type from object to string to use the string class.
    # round the coordinates to 6 digits
    for tag in ['lat', 'lon']:
      selected_centroids[tag] = round (selected_centroids[tag], 6)

    return selected_centroids


def read_input(input_str, sheet, header=None, index_col=None):
    '''
    This function is used for reading the input files, as of the first version of this script, there are only two .xlsx
    files that use this module. The solarTRACE file (currently pnnl_utility_timelines_summary.xlsx) and the berkley lab 
    files (queues_2021_clean_data.xlsx)

    Args:
        input_str: is a string that is meant to tell the module which input file is being read.
        sheet: denotes the excel sheet that holds the information needed for processing.
        header: is used for the solarTRACE data because they contain extra rows for headers.
        index_col: is used to indicate there is an index column in this file.

    Returns:
        returns: A Pandas dataframe(df) (The rest of the module only modifies this df)
    '''
    # centroids_reservations = pd.read_csv('AIANNHA_centroids.csv')[COLS]
    all_files = list(INPUT_DIR.glob('*'))
    for file in all_files: # Loop over all files
        if input_str in file.name: # Check if input string is in the file name
            print ('    {:s} includes {:s}'.format (file.name, input_str))
            xlsx = pd.ExcelFile(file) # Read the corresponding file
            print ('      create pandas xlsx')
            df = pd.read_excel(xlsx, sheet, header=header, index_col=index_col)
            print ('      read xlsx, header={:s}, index_col={:s}'.format (str(header), str(index_col)))
            if header is None and index_col is None:
                print ('      read xlsx without header/index_col')
                df = pd.read_excel(xlsx, sheet)
            return df
    return None

def add_state_full(df):
    '''
    This function is used to add states' spelled out name to the df using the centroids file. This is used for searching 
    through the API from the final_processing.py file.
    '''
    temp_df = df.copy()
    centroids = get_centroids()
    state_dict = centroids.set_index('STATE_ABBR')['STATE_NAME'].to_dict()
    temp_df.insert(1, 'state_full', df['state'].map(state_dict))
    return temp_df

API_TOTAL = 0
API_IDX = 0

def start_api_tracking(n):
    global API_TOTAL, API_IDX
    API_TOTAL = n
    API_IDX = 0

def get_api_result(row, bProgress=False):
    '''
    This function is used to call the api for one row. The for loop that goes over all the rows is in the 
    final_processing.py file implemented in the api_call function.
    '''
    global API_TOTAL, API_IDX
    try:
        if row.get('ahj') is None:
            return pd.Series([None, None])
        row_state = row[0]
        row_ahj = row[1].split()[:-1]
        response = requests.get(f'{API_STRING}&state={row_state}&city={row_ahj}')
        data = response.json()
        if data and len(data) >= 1:
            lat = round(float(data[0]['lat']),6)
            lon = round(float(data[0]['lon']),6)
            result = pd.Series([lat, lon])
            if bProgress:
                API_IDX += 1
                print ('      API request {:d} of {:d} returns [{:.6f},{:.6f}]'.format (API_IDX, API_TOTAL, lon, lat))
            return result
        else:
            return pd.Series([None, None])  # Default values

    except json.JSONDecodeError:  # Catch the exception
        return pd.Series([None, None])  # Return default values

def write_output(df, output_dir):
    df.fillna(0.0).to_csv(output_dir, index=False)
