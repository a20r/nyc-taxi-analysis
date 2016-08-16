
import common
import seaborn as sns
import matplotlib.pyplot as plt
import plotting
from matplotlib import animation
from JSAnimation import IPython_display
from datetime import timedelta, datetime


def plot_density(df, start_dt, end_dt, rtype, ax):
    params = {"dropoff": ("dropoff_datetime", "Dropoff Density",
                          common.get_dropoff_geos),
              "pickup": ("pickup_datetime", "Pickup Density",
                         common.get_pickup_geos)}
    ttype, tle, efunc = params[rtype]
    sdf = common.query_dates(df, start_dt, end_dt, ttype)
    data = efunc(sdf)
    ax = sns.kdeplot(data[:, 0], data[:, 1], shade=False, n_levels=25,
                     cmap="jet", ax=ax)
    minx, miny, maxx, maxy = common.MANHATTAN_POLY.bounds
    ax.set_title(tle)
    return ax


def make_density_plots(df, start_dt, end_dt, ax1, ax2):
    plotting.plot_manhattan(ax1)
    plot_density(df, start_dt, end_dt, "pickup", ax1)
    plotting.plot_manhattan(ax2)
    return plot_density(df, start_dt, end_dt, "dropoff", ax2)


def density_animation(df):
    minx, miny, maxx, maxy = common.MANHATTAN_POLY.bounds
    fig, axarr = plt.subplots(1, 2, figsize=(15, 10))
    dt = timedelta(minutes=10)
    start = datetime(2014, 1, 9, 0, 0)
    end = start + dt
    p = make_density_plots(df, start, end, axarr[0], axarr[1])
    n_frames = 200

    def init():
        return p

    def animate(i):
        for ax in axarr:
            ax.clear()
            ax.set_xlim(minx, maxx)
            ax.set_ylim(miny, maxy)
        st = start + timedelta(minutes=i)
        en = start + timedelta(minutes=i + 10)
        fig.suptitle(str(st), fontsize=24)
        return make_density_plots(df, st, en, axarr[0], axarr[1])

    return animation.FuncAnimation(fig, animate, init_func=init,
                                   frames=n_frames, interval=60)
