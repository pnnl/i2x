from pathlib import Path

# Define the components of the file path
SCRIPT_DIR = Path(__file__).resolve().parent # Get the directory that the current script is in
PARENT_DIR = SCRIPT_DIR.parent.parent # Get the parent directory
OUTPUT_DIR = PARENT_DIR / 'hubdata' / 'output' / 'queued_up.csv'# Get the output directory

def write_output(df):
    df.fillna(0.0).to_csv(OUTPUT_DIR, index=False)