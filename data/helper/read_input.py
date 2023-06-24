import pandas as pd
from pathlib import Path

# Define the components of the file path
SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
PARENT_DIR = SCRIPT_DIR.parent.parent # Get the parent directory
INPUT_DIR = PARENT_DIR / 'hubdata' / 'input' # Get the input directory

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

