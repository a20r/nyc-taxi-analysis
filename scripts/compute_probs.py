
import pandas as pd
import numpy as np
import tqdm
import common
from scipy.spatial import KDTree
from multiprocessing import Pool


stations = pd.read_csv("data/stations.csv")
stations_kd = KDTree(stations.as_matrix(["lng", "lat"]))
sts = stations.as_matrix(["lng", "lat"])
n_stations = stations.shape[0]
#df = common.load_data(nrows=50000, load=True)
df = common.load_data(nrows=30000000, load=True)
interval_length = 15
mins_per_day = 24 * 60
intervals_per_day = mins_per_day / interval_length
# 165114362
# 10000000


def calc_freqs(job_params):
    freqs = np.zeros((intervals_per_day, 7, n_stations, n_stations))
    j, rng = job_params
    for i in tqdm.tqdm(rng, position=j, desc="Job %d" % j,
                       dynamic_ncols=True, miniters=1):
        row = df.iloc[i]
        p_dt = row["pickup_datetime"]
        interval, wday = common.convert_date_to_interval(
            p_dt, interval_length)
        pickup = np.array([row["pickup_longitude"],
                           row["pickup_latitude"]])
        dropoff = np.array([row["dropoff_longitude"],
                            row["dropoff_latitude"]])
        _, p_label = stations_kd.query(pickup)
        _, d_label = stations_kd.query(dropoff)
        freqs[interval][wday][p_label][d_label] += 1
    return freqs


if __name__ == "__main__":
    n_workers = 8
    pool = Pool(n_workers)
    arrs = np.array_split(range(df.shape[0]), n_workers)
    arrs = map(list, arrs)
    print "Computing probabilities..."
    freqs = sum(pool.map(calc_freqs, list(enumerate(arrs))))
    print "Saving to file..."
    np.save("data/freqs.npy", freqs)
    pool.close()
