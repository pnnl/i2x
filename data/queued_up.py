from helper.get_centroids import get_centroids
from helper.read_input import read_input

QUEUED = 'queues'
QUEUED_SHEET = 'data'

def qu_driver():
    centroids = get_centroids()
    print("centroids: ",centroids)
    data_df = read_input(QUEUED, QUEUED_SHEET)
    print("data_df: ", data_df)