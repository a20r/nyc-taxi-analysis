
import common
import matplotlib.pyplot as plt
import numpy as np


def plot_density():
    df = common.load_data(nrows=100000)
    # start_dt = datetime(2014, 1, 10, 4, 0)
    # end_dt = datetime(2014, 1, 10, 4, 10)
    # df = common.query_dates(df, start_dt, end_dt, "dropoff_datetime")
    arr = common.get_pickup_geos(df)
    hm, xedges, yedges = np.histogram2d(arr[:, 0], arr[:, 1], bins=1000)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    plt.imshow(hm, extent=extent)
    plt.show()


if __name__ == "__main__":
    plot_density()
