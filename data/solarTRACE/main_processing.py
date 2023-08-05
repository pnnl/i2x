''' 
    Version 1.1 improvement: remove duplicated code by encapsulating
    the while loop.
'''

def total(df):
    # geo_grouped_df.iloc[:,[11, 18]]
    copy_df = df.copy()
    # Define your starting index (adjusting for 0-indexing in python)
    start_index = 11  # 12th column

    # Loop until there are no more pairs of columns
    while start_index + 14< len(copy_df.columns):
        # Calculate the other index (7 columns ahead)
        other_index = start_index + 7

        # Add the two columns together
        copy_df[f'total_{start_index+1}_{other_index+1}'] = copy_df.iloc[:, start_index] + copy_df.iloc[:, other_index]

        # Move to the next pair of columns
        start_index += 14
    return copy_df

def weighted_pre(df):
    copy_df = df.copy()
    # Define your starting index (adjusting for 0-indexing in python)
    start_index = 11  # 12th column
    start_index_2 = 12 # 13th column

    # Loop until there are no more pairs of columns
    while start_index + 14< len(copy_df.columns):
        # Calculate the other index (7 columns ahead)
        other_index = start_index + 7
        other_index_2 = start_index_2 + 7
        # Add the two columns together
        copy_df[f'Weighted_pre_IX_{start_index+1}_{other_index+1}'] = \
        ((copy_df.iloc[:, start_index] * copy_df.iloc[:, start_index_2]) + \
        (copy_df.iloc[:, other_index] * copy_df.iloc[:, other_index_2])) / \
        (df.iloc[:, start_index] + df.iloc[:, other_index])
        # Move to the next pair of columns
        start_index += 14
        start_index_2 += 14
    return copy_df

def full(df, total):
    copy_df = df.copy()
    # Define your starting index (adjusting for 0-indexing in python)
    start_index = 16  # 12th column
    start_index_2 = 17 # 13th column

    # Loop until there are no more pairs of columns
    while start_index + 14< len(total.columns):
        # Calculate the other index (7 columns ahead)
        other_index = start_index + 7
        other_index_2 = start_index_2 + 7
        # Add the two columns together
        copy_df[f'total_full_{start_index+1}-{start_index_2+1}+{other_index+1}-{other_index_2+1}'] = abs(total.iloc[:, start_index] - total.iloc[:, start_index_2]) + abs(total.iloc[:, other_index] - total.iloc[:, other_index_2])
        # Move to the next pair of columns
        start_index += 14
        start_index_2 += 14
    return copy_df