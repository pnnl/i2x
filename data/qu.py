from helper.get_centroids import get_centroids
from helper.read_input import read_input
from helper.write_output import write_output
from queued_up.initial_output import cleanup, init_output
from queued_up.solar_wind import final_output
QUEUED = 'queues'
QUEUED_SHEET = 'data'

def qu_driver():
    centroids = get_centroids()
    # print("centroids: ",centroids)
    input_df = read_input(QUEUED, QUEUED_SHEET)
    # print("data_df: ", data_df)
    clean_df = cleanup(input_df)
    # print("clean_df: ", data_df)
    initial_df = init_output(clean_df)
    # print("initial_df: ", initial_df)
    final_df = final_output(clean_df, initial_df)
    result = final_df.merge(centroids,  how = 'inner', on = ['state_county'])
    # print(result)
    write_output(result)


