
import numpy as np
import plotly
import plotly.graph_objs as go
import pandas as pd
import scipy.stats as stats
from flask import Flask, render_template, jsonify, Response


app = Flask(__name__, static_folder="visualizations")
freqs = np.load("data/freqs.npy")
n_stations = 101


def load_data(p_st, d_st):
    fname = "data/ts/{}-{}.txt".format(p_st, d_st)
    df_options = {"names": ["datetime"],
                  "parse_dates": ["datetime"],
                  "infer_datetime_format": True,
                  "header": None,
                  "squeeze": True,
                  "skip_blank_lines": True,
                  "index_col": 0}
    df = pd.read_csv(fname, **df_options)
    df.sort_index(inplace=True)
    return df


def hist(dts):
    bins = np.zeros((20,))
    for dt in dts:
        b = (dt.hour * 60 + dt.minute) / 72
        bins[b] += 1
    return bins


def get_cors(ps0, ds0, ps1, ds1):
    all_ts0 = load_data(ps0, ds0)
    all_ts1 = load_data(ps1, ds1)
    print len(all_ts0)
    print len(all_ts1)
    cors = np.zeros((365,))
    ps = np.zeros((365,))
    for i in xrange(365):
        dt = pd.Timedelta("1 day")
        st = pd.Timestamp("2014-01-01 00:00") + i * dt
        ed = st + dt
        d1 = all_ts0[st:ed].index
        d2 = all_ts1[st:ed].index
        ts1 = hist(d1)
        ts2 = hist(d2)
        cors[i], ps[i] = stats.pearsonr(ts1, ts2)
    return cors, ps


@app.route("/", methods=["GET"])
def get_index():
    return render_template("demand.html")


def generate_graph_div(ps0, ds0, ps1, ds1):
    cors, ps = get_cors(ps0, ds0, ps1, ds1)
    cor_scatter = go.Scatter(
        x=range(365), y=cors, mode="markers",
        name="Correlation"
    )

    p_scatter = go.Scatter(
        x=range(365), y=ps, mode="markers",
        name="P-Value"
    )

    title_desc = ("Correlation Over the Year "
                  "| Mean: {:.3f} | STD: {:.3f}".format(cors.mean(),
                                                        cors.std()))
    title_route = "Route 1: {} to {} | Route 2: {} to {}"\
        .format(ps0, ds0, ps1, ds1)
    title = title_desc + "<br>" + title_route

    layout = go.Layout(
        title=title,
        xaxis=dict(
            title="Day of Year"
        ),
        yaxis=dict(
            range=[-1, 1]
        )
    )
    fig = go.Figure(data=[cor_scatter, p_scatter], layout=layout)
    graph = plotly.offline.plot(fig, include_plotlyjs=False, output_type="div")
    return graph


@app.route("/graph/<ps0>/<ds0>/<ps1>/<ds1>", methods=["GET"])
def get_graph_div(ps0, ds0, ps1, ds1):
    return generate_graph_div(ps0, ds0, ps1, ds1)


@app.route("/correlations", methods=["GET"])
def get_correlation_page():
    ps0, ds0 = 32, 35
    ps1, ds1 = 56, 35
    graph = generate_graph_div(ps0, ds0, ps1, ds1)
    return render_template("correlations.html", graph=graph)


@app.route("/stations", methods=["GET"])
def get_stations():
    with open("data/stations.csv") as f:
        res = Response(f.read(), mimetype="text/csv")
        return res


@app.route("/js/<path:path>", methods=["GET"])
def get_js(path):
    with open("visualizations/js/" + path) as f:
        res = Response(f.read(), mimetype="text/javascript")
        return res


@app.route("/freqs/<int:interval>/<int:day>/<int:pick>", methods=["GET"])
def get_freqs(interval, day, pick):
    data = freqs[interval][day][pick]
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    time_fmt = "{} {:0>2}:{:0>2}"
    hrs = interval * 15 / (60)
    secs = interval * 15 % 60
    t = time_fmt.format(days[day], hrs, secs)
    return jsonify(freqs=list(data), time=t)


@app.route("/freqs/<int:n_inters>/<int:interval>/<int:day>/<int:pick>",
           methods=["GET"])
def get_multi_freqs(n_inters, interval, day, pick):
    if interval + n_inters > freqs.shape[0]:
        n_inters = freqs.shape[0] - interval - 1
    data = freqs[interval:(interval + n_inters)].sum(axis=0)[day][pick]
    print "Min: {}, Max: {}".format(data.min(), data.max())
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    time_fmt = "{} {:0>2}:{:0>2} - {:0>2}:{:0>2}"
    e_interval = interval + n_inters
    hrs = interval * 15 / (60)
    secs = interval * 15 % 60
    e_hrs = e_interval * 15 / (60)
    e_secs = e_interval * 15 % 60
    t = time_fmt.format(days[day], hrs, secs, e_hrs, e_secs)
    return jsonify(freqs=list(data), time=t)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082, debug=True)
