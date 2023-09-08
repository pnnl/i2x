FIRST = 'first'
OBJECT = 'object'
SUM = 'sum'
GEO_ID = 'geo_id'

def aggregate(df):
    '''
        This function groups the initial input by the GEO IDs. 
    '''
    agg_dict = {col: FIRST if df[col].dtype == OBJECT else SUM for col in df.columns}
    geo_grouped_df = df.groupby(GEO_ID).agg(agg_dict)
    return geo_grouped_df


def rename_cols(df):
    '''
    This function renames columns to better reflect each column's inherent characteristics.
    Ideally, seperation of PV and PV+Storage must also be added to column titles.
    '''
    # current column names
    cols = df.columns
    # first 12 columns are unique, save them
    new_cols = [str(x) for x in list(cols[:11])]
    # now remove them from the main cols
    cols = cols[11:]
    # prepare sizes and years
    sizes = ['0-10kW']*5 + ['11-50kW']*6  # 70 is the number of columns per each size
    years = ['2017', '2018', '2019', '2020', '2021']*28  # 28 is the number of columns per each year (one set)
    # starting from the 12th column, every 14 columns are for a specific year
    counter = 0
    # print('cols[:14]', cols[:14])
    for size, year in zip(sizes, years):
        for col in cols[:14]:  # 14 columns for each year
            new_col = f'{col}_{size}_{year}'
            new_cols.append(new_col)
            counter +=1
        cols = cols[14:]  # update the remaining columns for the next iteration
    # print('new_cols', new_cols)
    # assign the 12 initial columns back to the dataframe
    df.columns = new_cols
    return df