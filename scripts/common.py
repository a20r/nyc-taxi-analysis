
import pandas as pd
import time
import re
import json
import util
import shapely.geometry as geom


DATA_DIR = "/home/wallar/fast_data/"
DATA_FILENAME = "nyc_taxi_data.csv.gz"
HDF5_FILENAME = "nyc_taxi_store.h5"
DATA_PATH = DATA_DIR + DATA_FILENAME
HDF5_PATH = DATA_DIR + HDF5_FILENAME
NFS_PATH = "/home/wallar/nfs/data/data-sim/"
# DATA_PATH = DATA_DIR + "nyc_small.csv"

NYC_DIR = "data/nyc-graph/{}.csv"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
fn_probs_fields = ["time_interval", "day", "pickup", "dropoff", "probability"]
fn_freqs_fields = ["time_interval", "day", "expected_requests"]
fn_probs = "data/probs.csv"
fn_freqs = "data/freqs.csv"
nyc_poly = None


def get_metrics(n_vehicles, cap, waiting_time, predictions):
    m_file = NFS_PATH + "v{}-c{}-w{}-p{}/metrics_pnas.csv".format(
        n_vehicles, cap, waiting_time, predictions)
    df = pd.read_csv(m_file)
    df.sort_values("time", inplace=True)
    df.reset_index(inplace=True)

    # REMEMBER TO REMOVE THIS SHIT
    df = query_dates(df, "2013-05-05", "2013-05-05 01:09:00", "time")
    # REMEBER THIS SHIT ABOVE

    df["rolling_serviced_percentage"] = df["n_pickups"] \
        / (df["n_pickups"] + df["n_ignored"])
    df["mean_travel_delay"] = df["mean_delay"] - df["mean_waiting_time"]
    df["serviced_percentage"] = df["n_pickups"].sum() / \
        (df["n_ignored"].sum() + df["n_pickups"].sum())
    df["km_travelled_per_car"] = df["total_km_travelled"] / df["n_vehicles"]
    df["n_shared_perc"] = df["n_shared"] / (df["n_shared"] + df["time_pass_1"])
    df.drop("Unnamed: 0", axis=1, inplace=True)
    df.drop("capacity", axis=1, inplace=True)
    df.drop("is_long", axis=1, inplace=True)
    df.drop("n_vehicles", axis=1, inplace=True)
    return df


def convert_date_to_interval(str_time, interval):
    t = time.strptime(str_time, DATE_FORMAT)
    secs = t.tm_hour * 60 * 60 + t.tm_min * 60 + t.tm_sec
    return secs / (interval * 60), t.tm_wday


def get_nyc_poly():
    global nyc_poly
    if nyc_poly is None:
        with open("data/nyc_poly.kml") as fin:
            data = fin.read()
            cs = re.findall(r"<coordinates>[\s\S]*?<\/coordinates>", data)[0] \
                .split("<coordinates>")[1]\
                .split(",0 ")[:-2]
            poly = list()
            for gs in cs:
                coords = map(float, gs.strip().split(","))
                poly.append(coords)
            nyc_poly = geom.Polygon(poly)
    return nyc_poly


def get_nyc_geojson():
    with open("sandbox/nyc.geo.json") as f:
        nyc_dict = json.loads(f.read())
        nyc_poly = geom.shape(nyc_dict["geometry"])
        return nyc_poly


def get_dropoff_geos(df):
    return df.as_matrix(["dropoff_longitude", "dropoff_latitude"])


def get_pickup_geos(df):
    return df.as_matrix(["pickup_longitude", "pickup_latitude"])


def query_dates(df, start, end, header):
    qstr = "'{}' <= {} < '{}'".format(str(start), str(header), str(end))
    return df.query(qstr)


def within_region(lons, lats):
    nyc = get_nyc_poly()
    bools = list()
    for lon, lat in zip(lons, lats):
        bools.append(nyc.contains(geom.Point(lon, lat)))
    return bools


@util.profile()
def load_data_within_time(min_time, max_time):
    pass


def clean_df(df):
    d_qstr = "dropoff_latitude != 0 and dropoff_longitude != 0"
    p_qstr = "pickup_latitude != 0 and pickup_longitude != 0"
    df.query(d_qstr, inplace=True)
    df.query(p_qstr, inplace=True)
    df = df[within_region(df["pickup_longitude"], df["pickup_latitude"])]
    df = df[within_region(df["dropoff_longitude"], df["dropoff_latitude"])]
    return df


@util.profile()
def load_data(chunksize):
    dfs = pd.read_csv(DATA_PATH, parse_dates=True, infer_datetime_format=True,
                      chunksize=chunksize, engine="python")
    return dfs
