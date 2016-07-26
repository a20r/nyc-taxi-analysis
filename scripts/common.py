
import pandas as pd
import numpy as np
import os.path
import warnings
import logging
import util
import shapely.geometry as geom


DATA_DIR = "/media/wallar/storage/data/"
DATA_FILENAME = "nyc_taxi_data.csv.gz"
HDF5_FILENAME = "nyc_taxi_store.h5"
DATA_PATH = DATA_DIR + DATA_FILENAME
HDF5_PATH = DATA_DIR + HDF5_FILENAME

MANHATTAN_POLY = geom.Polygon([(-74.0299987793, 40.6859677292),
                               (-73.8500976562, 40.6859677292),
                               (-73.8500976562, 40.9145503627),
                               (-74.0299987793, 40.9145503627)])


def get_dropoff_geos(df):
    return df.as_matrix(["dropoff_latitude", "dropoff_longitude"])


def get_pickup_geos(df):
    return df.as_matrix(["pickup_latitude", "pickup_longitude"])


def query_dates(df, start, end, header):
    qstr = "'{}' < {} < '{}'".format(str(start), str(header), str(end))
    return df.query(qstr)


def within_region(lons, lats):
    bools = list()
    for lon, lat in zip(lons, lats):
        bools.append(MANHATTAN_POLY.contains(geom.Point(lon, lat)))
    return bools


@util.profile()
def load_data(nrows=None, load=False, bounding_box=MANHATTAN_POLY):
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
        df = pd.read_csv(DATA_PATH, nrows=nrows, parse_dates=True,
                         infer_datetime_format=True, engine="c")
        d_qstr = "dropoff_latitude != 0 and dropoff_longitude != 0"
        p_qstr = "pickup_latitude != 0 and pickup_longitude != 0"
        # poly_pick_qstr = "@within_region(pickup_latitude, pickup_longitude)"
        df.query(d_qstr, inplace=True)
        df.query(p_qstr, inplace=True)
        df = df[within_region(df["pickup_longitude"], df["pickup_latitude"])]
        df = df[within_region(df["dropoff_longitude"], df["dropoff_latitude"])]
        logging.info("Writing to store")
        df.to_hdf(HDF5_PATH, "table", mode="w", append=False)
        return df
