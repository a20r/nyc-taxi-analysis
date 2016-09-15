
import sklearn.neighbors as nn
import numpy as np
import pandas as pd
from common import NYC_DIR


def find_clusters(geos, tol):
    hav_tol = tol / 6371.0
    used = [False] * len(geos)
    ball_tree = nn.BallTree(np.radians(geos), metric="haversine")
    centers = list()
    for i in xrange(len(geos)):
        if not used[i]:
            loc = geos[i]
            st = np.array([i, loc[0], loc[1]])
            centers.append(st)
            nearest = ball_tree.query_radius([np.radians(loc)], hav_tol)[0]
            for i in nearest:
                used[i] = True
    return np.array(centers)


if __name__ == "__main__":
    nyc_nodes = pd.read_csv(NYC_DIR.format("points"),
                            names=["id", "lat", "lon"])
    nyc_mat = nyc_nodes.as_matrix(["lon", "lat"])
    stations = find_clusters(nyc_mat, 0.45)
    np.savetxt("data/stations.csv", stations, delimiter=",",
               header="id,lng,lat", fmt=["%d", "%.18f", "%.18f"], comments="")
    print "Stations:", len(stations)
