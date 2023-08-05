def aggregate(df):
    agg_dict = {col: 'first' if df[col].dtype == 'object' else 'sum' for col in df.columns}
    geo_grouped_df = df.groupby('geo_id').agg(agg_dict)
    return geo_grouped_df

def rename_cols(df):
    # current column names
    cols = df.columns
    # first 12 columns are unique, save them
    new_cols = [str(x) for x in list(cols[:11])]
    # now remove them from the main cols
    cols = cols[11:]
    # prepare sizes and years
    sizes = ['0-10kW']*5 + ['11-50kW']*6  # 70 is the number of columns per each size
    years = ['2017', '2018', '2019', '2020', '2021']*28  # 28 is the number of columns per each year
    # starting from the 13th column, every 14 columns are for a specific year
    counter = 0
    for size, year in zip(sizes, years):
        for col in cols[:14]:  # 14 columns for each year
            new_cols.append(f'{col}_{size}_{year}')
            counter +=1
        cols = cols[14:]  # update the remaining columns for the next iteration
    # assign the 12 initial columns back to the dataframe
    df.columns = new_cols
    return df