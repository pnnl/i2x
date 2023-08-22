import pandas as pd

ENERGY_TYPE_LIST = ["Solar", "Wind", "Neither"]
STATUS_LIST = ["withdrawn","operational", "active", "suspended"]
BASE = 'state_county'
PARAMETER = 'project_name'
BASE_COL = 'state_county'
COL = ['mw1', 'mw2']

def final_output(clean_df, initial_df):
    result_col =list()
    col_names = []
    for each_type in ENERGY_TYPE_LIST:
        for each_status in STATUS_LIST:
            col_names.append("_".join(["proj_count", "_".join([each_type, each_status])]))
            result_col.append(proj_count(BASE, PARAMETER, clean_df, each_type, each_status))

    result_col_mw = list()
    col_names_mw = list()
    for each_type in ENERGY_TYPE_LIST:
        for each_status in STATUS_LIST:
            col_names_mw.append("_".join(["mw", "_".join([each_type, each_status])]))
            result_col_mw.append(megawatt_max(BASE_COL, COL, clean_df, each_type, each_status))

    queued_up_combos = pd.concat(result_col, axis=1, keys=col_names).reset_index().fillna(0)
    queued_up_combos = queued_up_combos.fillna(0)
    queued_up_combos_mw = pd.concat(result_col_mw, axis=1, keys=col_names_mw).reset_index().fillna(0)
    queued_up_combos_mw = queued_up_combos_mw.fillna(0)

    queued_up_temp = pd.merge(initial_df, queued_up_combos_mw, how='outer', on='state_county')
    queued_up_final = pd.merge(queued_up_temp, queued_up_combos, how='outer', on='state_county')
    queued_up_final['state_county'] = queued_up_final.state_county.astype('string')
    return queued_up_final


def proj_count(parameter, col, df, energy_type, status):
    if energy_type == "neither":
        result = df[~df.type_clean.str.contains("Wind|Solar").fillna(False)]
    else:
        result = df[df.type_clean.str.contains(energy_type).fillna(False)]
    result = result[result.q_status.str.contains(status)]
    result = result.groupby([parameter])[col].count()
    return result

def megawatt_max(base, c, df, energy_type, status):
    if energy_type == "neither":
        result = df[~df.type_clean.str.contains("Wind|Solar").fillna(False)]
    else:
        result = df[df.type_clean.str.contains(energy_type).fillna(False)]
    result = result[result.q_status.str.contains(status)]
    result = result.groupby([base]).sum(numeric_only=True)
    result = result[c].max(axis=1)
    return result