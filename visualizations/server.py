
import numpy as np
from flask import Flask, render_template, jsonify, Response


app = Flask(__name__, static_folder="visualizations")
freqs = np.load("data/freqs.npy")


@app.route("/", methods=["GET"])
def get_index():
    return render_template("demand.html")


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
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
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
