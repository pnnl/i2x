import pandas as pd

COLS = ["q_status", "q_date", "on_date", "project_name", "utility", "county_1", "type_clean", "mw1", "mw2", "state"]

'''
    This function does initial cleanup
    1. Formats date columns to datetime
    2. Calculate num of days between on_date and q_date
    3. Fills empty entries with 0.0s and Unknowns
    4. combines state abbr and county name into "state_county" column with values [state abbreviation]_[county name]
    5. Removes entries with 0 or negative mw from the mw1 column since we are not interested in those data at this point
'''
def cleanup(df):
    df = df[COLS]
    # Convert "q_date" column to date/time format (NOTE: There is no time section)
    df['q_date'] = pd.to_datetime(df['q_date'], errors='coerce')
    # Convert "on_date" column to date/time format (NOTE: Only 1571 entries have on_date)
    df['on_date'] = pd.to_datetime(df['on_date'], errors='coerce')
    # Count number of days between on_date and q_date
    df['num_days'] = (df['on_date']-df['q_date']).dt.days
    # Fill the NaN values with respective defaults
    df['mw2'] = df['mw2'].fillna(0.0)
    df['mw1'] = df['mw1'].fillna(0.0)
    df['num_days'] = df['num_days'].fillna(0.0)
    df['project_name'] = df['project_name'].fillna('UNKNOWN')
    # create a state_county Column as a pseudo unique identifier for each row
    df['state_county'] = df.state.str.cat(df.county_1, sep='_')
    # Remove 'mw1's with 0 or negative values.
    df = df[df['mw1']>0]

    return df


def init_output(df):
    '''
    This function uses the state_county column to group then aggregate according to:
    1. Get the sum for mw1 nad mw2
    2. Get max between mw1 and mw2
    3. Get max of num_days
    4. Get project counts
    5. *Get q_status counts
    6. Concatenate all the entries of type_clean column for each grouping of state_county
    7. Want type_clean in alphabetical order
    '''
    # Count utilities 
    utility_count = df.groupby(['state_county'])['utility'].nunique()
    # Aggregate counties and sum all the floating point columns per county (NOTE: only mw1 and mw2 are summed.)
    # print(df)
    mw_sum = df.groupby(['state_county']).sum(numeric_only=True)
    # Get max of mw1 and mw2
    mw_max = mw_sum[['mw1', 'mw2']].max(axis=1)
    # Aggregate counties and take the max of the days for each county
    days = df.groupby(['state_county'])['num_days'].max()
    # Get project counts
    project_count = df.groupby(['state_county'])['project_name'].count()
    # Get status counts --> ADD????????????????????????????????
    status_count = df.groupby(['state_county'])['q_status'].count()
    # Aggregate types of energy generation for each
    type_clean = df.fillna('Unknown').groupby('state_county').agg({'type_clean': lambda d: ", ".join(sorted(set(d)))}).reset_index()
    # format type_clean to match the previous pd series with state_county as index
    type_clean = type_clean.set_index('state_county')
    # Combine the series to create an intitial version of the queued up output
    queued_up_initial = pd.concat([utility_count, mw_max, project_count, days, type_clean['type_clean']], axis=1, keys=['utility_count', 'mw_max', 'project_count', 'days_max', 'type_clean']).reset_index()
    
    return queued_up_initial 

