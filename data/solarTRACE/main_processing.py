
def total(df):
    '''
    This function calculates the addition of Installs (Installs columns) by adding the PV and PV+storage 
    values for the installs columns for each year.
'''
    copy_df = df.copy()
    # Define your starting index (adjusting for 0-indexing in python)
    start_index = 11  # 12th column
    # Loop until there are no more pairs of columns
    while start_index + 14< len(copy_df.columns):
        # Calculate the other index (7 columns ahead)
        other_index = start_index + 7
        # Add the two columns together
        copy_df[f'Installs_{copy_df.iloc[:, start_index].name}'] = copy_df.iloc[:, start_index] + copy_df.iloc[:, other_index]
        # Move to the next pair of columns
        start_index += 14

    return copy_df


def weighted_pre(df):
    '''
    This function calculates the following weighted formula:
    [(Installs*Pre Ix)+(installs*Pre Ix)]/(Installs+Installs)
    based on:
    [(PV)+(PV&Storage)]/(PV+PV&Storage)
    respectively.
    '''
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
        copy_df[f'Weighted_{copy_df.iloc[:, start_index].name.split("_")[0]}_{copy_df.iloc[:, start_index_2].name}'] = \
        ((copy_df.iloc[:, start_index] * copy_df.iloc[:, start_index_2]) + \
        (copy_df.iloc[:, other_index] * copy_df.iloc[:, other_index_2])) / \
        (df.iloc[:, start_index] + df.iloc[:, other_index])
        # Move to the next pair of columns
        start_index += 14
        start_index_2 += 14

    return copy_df


def full(df, total):
    '''
    This function calculates based on:
    (Full IX - Total IX) + (Full IX - Total IX)
    '''
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
        copy_df[f'Add_{total.iloc[:, start_index].name.split("_")[0]}_{total.iloc[:, start_index_2].name}'] = abs(total.iloc[:, start_index] - total.iloc[:, start_index_2]) + abs(total.iloc[:, other_index] - total.iloc[:, other_index_2])
        # Move to the next pair of columns
        start_index += 14
        start_index_2 += 14

    return copy_df