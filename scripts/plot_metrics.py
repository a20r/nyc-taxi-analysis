
import matplotlib.pyplot as plt
import os
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
          "km_travelled_per_car", "n_shared_per_passenger", "comp_time"]

titles = ["Mean service rate", "Mean in-car travel delay $\delta$ - $\omega$",
          "Mean waiting time $\omega$", "Mean distance travelled",
          "Percentage of shared rides", "Mean computation time"]


vehicles = [1000, 2000, 3000]
caps = [2, 4]
days = [1, 2]
waiting_times = [300]
predictions = [-1, 0, 200, 400]
fancy_preds = ["No Rebalancing", 0, 200, 400]
# predictions = [0, 200, 400]
# fancy_preds = [0, 200, 400]



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
               "comp_time": "Mean Comp. Time [s]"}


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
            try:
                subdf = common.get_metrics_day(v, c, wt, p, d)
                dfs.append(subdf)
            except IOError:
                print "Error:", v, c, wt, p, d
        df = pd.concat(dfs)
        df.to_csv(cache_fn)
        return df


def _make_all_pred_plots(big_d, time_d, fig_name):
    fig, axarr = plt.subplots(2, 3, figsize=(11, 5))
    axarr = np.ravel(axarr)
    letters = "abcdef"
    for i, (field, ax) in enumerate(zip(fields, axarr)):
        title = "({}) {}".format(letters[i], titles[i])
        if i < 5:
            ax = sns.pointplot(x="n_vehicles", y=field, hue="predictions",
                               data=big_d, palette=clrs, ax=ax)
        else:
            ax =sns.pointplot(x="vehicles", y=field, hue="predictions",
                              data=time_d, palette=clrs, ax=ax)
        ax.set_xticklabels(vehicles)
        ax.set_title(title, fontsize=13, y=-0.45)
        ax.set_ylabel(prettify(field))
        ax.set_xlabel("Number of Vehicles")
        if "%" in prettify(field):
            ax.set_ylim([0, 1])
            vals = ax.get_yticks()
            ax.set_yticklabels(['{:3.0f}%'.format(x * 100) for x in vals])
        handles, _ = ax.get_legend_handles_labels()
        ax.legend().remove()
    fig.subplots_adjust(wspace=0.4, hspace=0.58)
    lgd = fig.legend(
        handles,
        fancy_preds,
        loc="lower center", fancybox=True,
        bbox_to_anchor=(0.46, 0.96),
        title="Number of Samples", markerscale=2.5, ncol=4)
    fig.savefig(
        fig_dir + fig_name,
        bbox_inches='tight', bbox_extra_artists=(lgd,))
    plt.close()


def make_all_pred_plots(big_d, time_d):
    for field in fields:
        print field
        if field == "comp_time":
            handles = make_pred_plot(time_d, field)
        else:
            handles = make_pred_plot(big_d, field)
    return handles


def make_pred_plot(df, field):
    fig, axs = plt.subplots(1, 2, figsize=(4, 2), sharey=True, sharex=True)
    for c, ax in zip(caps, axs):
        subdf = df.query("capacity == {}".format(c))
        ax = sns.pointplot(x="vehicles", y=field, hue="predictions",
                           data=subdf, palette=clrs, ax=ax)
        ax.set_xticklabels(vehicles)
        ax.set_title("Capacity: {}".format(c))
        # ax.set_ylabel(prettify(field))
        if "%" in prettify(field):
            ax.set_ylim([0, 1])
            vals = ax.get_yticks()
            ax.set_yticklabels(['{:3.0f}%'.format(x * 100) for x in vals])
        ax.legend().remove()
        if c == 2:
            lbl = ax.set_xlabel("Number of Vehicles", x=1.1)
            lbl.set_horizontalalignment("center")
            ax.set_ylabel(prettify(field))
        else:
            ax.set_xlabel("")
            ax.set_ylabel("")
    fig.savefig(fig_dir + field + ".pdf", bbox_inches="tight")
    return ax.get_legend_handles_labels()[0]


def make_legend(handles):
    figlegend = plt.figure()
    lgd = figlegend.legend(
        handles,
        fancy_preds,
        loc="upper left",
        ncol=4,
        title="Number of Samples", markerscale=1.8, fontsize=14)
    lgd.get_title().set_fontsize(16)
    fname = fig_dir + "legend.pdf"
    figlegend.savefig(fname, bbox_inches="tight")
    os.system("pdfcrop {0} {0}".format(fname))


if __name__ == "__main__":
    sns.set_context("paper", font_scale=1.6)
    big_d = get_big_d(use_cache=True)
    time_d = pd.read_csv("data/times.csv")
    # handles = make_all_pred_plots(big_d, time_d)
    handles = make_pred_plot(big_d, "mean_waiting_time")
    make_legend(handles)
