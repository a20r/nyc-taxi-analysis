
import pandas as pd
import time
import os.path
import re
import json
import warnings
import logging
import util
import shapely.geometry as geom


DATA_DIR = "/home/wallar/fast_data/"
DATA_FILENAME = "nyc_taxi_data.csv.gz"
HDF5_FILENAME = "nyc_taxi_store.h5"
DATA_PATH = DATA_DIR + DATA_FILENAME
HDF5_PATH = DATA_DIR + HDF5_FILENAME
# DATA_PATH = DATA_DIR + "nyc_small.csv"

NYC_DIR = "data/nyc-graph/{}.csv"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
fn_probs_fields = ["time_interval", "day", "pickup", "dropoff", "probability"]
fn_freqs_fields = ["time_interval", "day", "expected_requests"]
fn_probs = "data/probs.csv"
fn_freqs = "data/freqs.csv"
nyc_poly = None


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
    qstr = "'{}' < {} < '{}'".format(str(start), str(header), str(end))
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
def load_data_bad(nrows=None, load=False, chunksize=None):
    warnings.simplefilter('ignore')
    need_to_reload = False
    if os.path.isfile(HDF5_PATH) and not load:
        df = pd.read_hdf(HDF5_PATH, "table")
        actual_rows = df.shape[0]
        if nrows < actual_rows:
            return df.head(nrows)
        elif nrows == actual_rows:
            return df
        else:
            need_to_reload = True
    if not os.path.isfile(HDF5_PATH) or need_to_reload or load:
        logging.info("Loading DataFrame")
        dfs = pd.read_csv(DATA_PATH, parse_dates=True, chunksize=chunksize,
                         infer_datetime_format=True, engine="python")
        # df = pd.read_csv(DATA_PATH, parse_dates=True, nrows=nrows,
        #                  infer_datetime_format=True, engine="python")
        for df in dfs:
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
    # for df in dfs:
    #     d_qstr = "dropoff_latitude != 0 and dropoff_longitude != 0"
    #     p_qstr = "pickup_latitude != 0 and pickup_longitude != 0"
    #     df.query(d_qstr, inplace=True)
    #     df.query(p_qstr, inplace=True)
    #     df = df[within_region(df["pickup_longitude"], df["pickup_latitude"])]
    #     df = df[within_region(df["dropoff_longitude"], df["dropoff_latitude"])]
    #     yield df
