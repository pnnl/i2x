from helper.get_centroids import get_centroids
from helper.read_input import read_input
import pandas as pd

QUEUED = 'queues'
QUEUED_SHEET = 'data'

def qu_driver():
    centroids = get_centroids()
    # print("centroids: ",centroids)
    data_df = read_input(QUEUED, QUEUED_SHEET)
    # print("data_df: ", data_df)
    dt_df = cleanup(data_df)
    # print("clean_df: ", dt_df)
    data_df = calc_days(dt_df)
    # print("clean_df: ", data_df)


def calc_days(df):
    df['num_days'] = (df['on_date']-df['q_date']).dt.days
    # Fill the NaN values with zeros
    df['num_days'] = df['num_days'].fillna(0.0)
    return df


def cleanup(df):
    # excel_data_df = pd.read_excel(r'\i2x\hubdata\SolarTRACE data 7-8-22.xlsx', sheet_name='Employees')
    cols = ["q_status", "q_date", "on_date", "project_name", "utility", "county_1", "type_clean", "mw1", "mw2", "state"]
    df = df[cols]
    # Convert "q_date" column to date/time format (NOTE: There is no time section)
    df['q_date'] = pd.to_datetime(df['q_date'], errors='coerce')
    # Convert "on_date" column to date/time format (NOTE: Only 1571 entries have on_date)
    df['on_date'] = pd.to_datetime(df['on_date'], errors='coerce')
    # Fill the NaN values with respective defaults
    df['mw2'] = df['mw2'].fillna(0.0)
    df['mw1'] = df['mw1'].fillna(0.0)
    df['project_name'] = df['project_name'].fillna('UNKNOWN')
    return df