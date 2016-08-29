
import pandas as pd
import numpy as np
import tqdm
import common
from scipy.spatial import KDTree
from multiprocessing import Pool


stations = pd.read_csv("data/stations.csv")
stations_kd = KDTree(stations.as_matrix(["lon", "lat"]))
n_stations = stations.shape[0]
df = common.load_data(nrows=10000000)
# 165114362
# 10000000


def calc_freqs(job_params):
    freqs = np.zeros((n_stations, n_stations))
    j, rng = job_params
    for i in tqdm.tqdm(rng, position=j, desc="Job %d" % j,
                       dynamic_ncols=True, miniters=10):
        row = df.iloc[i]
        pickup = np.array([row["pickup_longitude"],
                           row["pickup_latitude"]])
        dropoff = np.array([row["dropoff_longitude"],
                            row["dropoff_latitude"]])
        _, p_label = stations_kd.query(pickup)
        _, d_label = stations_kd.query(dropoff)
        freqs[p_label][d_label] += 1
    return freqs


if __name__ == "__main__":
    pool = Pool(8)
    arrs = np.array_split(range(df.shape[0]), 8)
    arrs = map(list, arrs)
    freqs = sum(pool.map(calc_freqs, list(enumerate(arrs))))
    #freqs = calc_freqs(arrs[0])
    probs = freqs / freqs.sum(axis=0)
    header = ",".join(str(i) for i in xrange(n_stations))
    np.savetxt("data/probs.csv", probs, delimiter=",",
               header=header, comments="")
    pool.close()
