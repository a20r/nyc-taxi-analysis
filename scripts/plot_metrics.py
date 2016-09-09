
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import common
import pandas as pd
import tqdm
from itertools import product

fig_dir = "/home/wallar/projects/sharedRide/paper-pred/figs/results/"


cache_fn = "data/metrics-cache.csv"


fields = ["mean_waiting_time", "mean_passengers", "mean_delay", "n_pickups",
          "mean_travel_delay", "serviced_percentage", "total_km_travelled",
          "km_travelled_per_car", "empty_rebalancing",
          "empty_moving_to_pickup", "empty_waiting", "not_empty",
          "active_taxis", "n_shared", "n_shared_per_passenger"]


fields = ["serviced_percentage", "mean_travel_delay", "mean_waiting_time",
          "km_travelled_per_car", "n_shared_per_passenger",
          "mean_waiting_time"]


vehicles = [1000, 2000, 3000]
caps = [4]
days = [1, 2]
waiting_times = [300]
predictions = [-1, 0, 200, 400]
fancy_preds = ["N.R.", 0, 200, 400]


has_legend = ["mean_waiting_time", "comp_time"]


pretty_dict = {"n_pickups": "Number of Pickups",
               "n_shared": "Number of Shared Rides",
               "n_shared_per_passenger": "% of Shared Rides",
               "mean_waiting_time": "Mean Waiting Time [s]",
               "mean_delay": "Mean Delay [s]",
               "mean_travel_delay": "Mean Travel Delay [s]",
               "n_shared_perc": "% of Shared Trips",
               "km_travelled_per_car": "Mean Dist. Travelled [km]",
               "serviced_percentage": "% Serviced Reqs.",
               "comp_time": "Mean Computational Time [s]"}


clrs = [sns.xkcd_rgb["grey"], sns.xkcd_rgb["sky blue"],
        sns.xkcd_rgb["bright red"], sns.xkcd_rgb["black"]]


def prettify(text):
    if text in pretty_dict.keys():
        return pretty_dict[text]
    else:
        words = text.split("_")
        return " ".join(w.capitalize() for w in words)


def get_big_d(use_cache=False):
    if use_cache:
        return pd.read_csv(cache_fn)
    else:
        dfs = list()
        prod = product(vehicles, caps, waiting_times, predictions, days)
        for v, c, wt, p, d in prod:
            subdf = common.get_metrics_day(v, c, wt, p, d)
            dfs.append(subdf)
        df = pd.concat(dfs)
        df.to_csv(cache_fn)
        return df


def make_pred_plots(big_d):
    fig, axarr = plt.subplots(2, 3, figsize=(11, 5))
    axarr = np.ravel(axarr)
    for i, (field, ax) in enumerate(zip(fields, axarr)):
        ax = sns.pointplot(x="n_vehicles", y=field, hue="predictions",
                           data=big_d, palette=clrs, ax=ax)
        ax.set_ylabel(prettify(field))
        if i >= 3:
            ax.set_xlabel("Number of Vehicles")
        else:
            ax.set_xlabel("")
        if "%" in prettify(field):
            ax.set_ylim([0, 1])
            vals = ax.get_yticks()
            ax.set_yticklabels(['{:3.0f}%'.format(x * 100) for x in vals])
        handles, _ = ax.get_legend_handles_labels()
        ax.legend().remove()
    fig.subplots_adjust(wspace=0.4, hspace=0.2)
    lgd = fig.legend(
        handles,
        fancy_preds,
        loc="lower center", fancybox=True,
        bbox_to_anchor=(0.46, 0.93),
        title="N. Predictions", markerscale=2.5, ncol=4)
    fig.savefig(
        fig_dir + "c4-results.pdf".format(field),
        bbox_inches='tight', bbox_extra_artists=(lgd,))
    plt.close()


if __name__ == "__main__":
    sns.set_context("paper", font_scale=1.7)
    big_d = get_big_d(use_cache=False)
    make_pred_plots(big_d)
