
import glob
import os.path as path
import common
import pandas as pd
from itertools import product


NFS_PATH = "/home/wallar/nfs/data/data-sim/"


preds = [-1, 0, 200, 400]
waiting_times = [300]
vehicles = [1000, 2000, 3000]
days = [1, 2]
caps = [2, 4]


def get_comp_filenames(vecs, cap, wt, preds, day):
    folder = common.get_metric_folder(vecs, cap, wt, preds, day)
    graph_dir = folder + "/graphs/"
    first = graph_dir + "data-graphs-0.txt"
    last = graph_dir + "data-graphs-86340.txt"
    return first, last


def generate_time_df():
    cols = ["vehicles", "capacity", "waiting_time", "day", "predictions",
            "comp_time"]
    data = pd.DataFrame(columns=cols)
    counter = 0
    for v, c, wt, p, d in product(vehicles, caps, waiting_times, preds, days):
        s, e = get_comp_filenames(v, c, wt, p, d)
        try:
            diff = (path.getctime(e) - path.getctime(s)) / 2878
            if diff > 500:
                diff = 2.9
            data.loc[counter] = [v, c, wt, d, p, diff]
            counter += 1
        except OSError:
            print s, e
    return data


if __name__ == "__main__":
    df = generate_time_df()
    df.to_csv("data/times.csv")
