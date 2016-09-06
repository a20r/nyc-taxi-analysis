
import matplotlib.pyplot as plt
import seaborn as sns
import common
import pandas as pd
import tqdm
from itertools import product

cache_fn = "data/metrics-cache.csv"


fields = ["mean_waiting_time", "mean_passengers", "mean_delay", "n_pickups",
          "mean_travel_delay", "serviced_percentage", "total_km_travelled",
          "km_travelled_per_car", "empty_rebalancing",
          "empty_moving_to_pickup", "empty_waiting", "not_empty",
          "active_taxis", "n_shared", "n_shared_per_passenger"]


vehicles = [1000, 2000, 3000]
caps = [4]
days = [1]
waiting_times = [300]
predictions = [-1, 0, 200, 400, 600]
fancy_preds = ["NR", 0, 200, 400, 600]


pretty_dict = {"n_pickups": "Number of Pickups",
               "n_shared": "Number of Shared Rides"}

pretty_dict = {"n_pickups": "Number of Pickups",
               "n_shared": "Number of Shared Rides",
               "n_shared_per_passenger": "% of Shared Rides",
               "mean_waiting_time": "Mean Waiting Time [s]",
               "mean_delay": "Mean Delay [s]",
               "mean_travel_delay": "Mean Travel Delay [s]",
               "n_shared_perc": "% of Shared Trips",
               "km_travelled_per_car": "Mean Distance Travelled [km]",
               "serviced_percentage": "% Serviced Requests",
               "comp_time": "Mean Computational Time [s]"}


clrs = [sns.xkcd_rgb["black"], sns.xkcd_rgb["sky blue"],
        sns.xkcd_rgb["bright red"]]


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
            dfs.append(common.get_metrics_day(v, c, wt, p, d))
        df = pd.concat(dfs)
        df.to_csv(cache_fn)
        return df


def make_pred_plots(big_d):
    pbar = tqdm.tqdm(fields, desc=fields[0])
    for field in pbar:
        pbar.set_description(field)
        fig = plt.figure()
        fig.set_size_inches(13, 10)
        ax = sns.pointplot(x="predictions", y=field, hue="n_vehicles",
                           data=big_d, palette=clrs)
        ax.set_xticklabels(fancy_preds)
        ax.set_ylabel(prettify(field))
        ax.set_xlabel("Number of Predictions")
        if "%" in prettify(field):
            ax.set_ylim([0, 1])
            vals = ax.get_yticks()
            ax.set_yticklabels(['{:3.0f}%'.format(x * 100) for x in vals])
        handles, _ = ax.get_legend_handles_labels()
        plt.legend(
            handles,
            vehicles,
            loc="center left", fancybox=True,
            shadow=True, bbox_to_anchor=(1, 0.5),
            title="N. Vehicles", markerscale=2)
        plt.savefig(
            "figs/avg-with-preds-{}.png".format(field),
            bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    sns.set_context("poster", font_scale=1.5)
    big_d = get_big_d(use_cache=True)
    make_pred_plots(big_d)
