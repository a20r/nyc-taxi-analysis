
import pandas as pd


DATA_DIR = "/media/wallar/storage/data/"
DATA_FILENAME = "nyc_taxi_data.csv.gz"
DATA_PATH = DATA_DIR + DATA_FILENAME


def get_dropoff_geos(df):
    return df.as_matrix(["dropoff_latitude", "dropoff_longitude"])


def get_pickup_geos(df):
    return df.as_matrix(["pickup_latitude", "pickup_longitude"])


def query_dates(df, start, end, header):
    qstr = "'{}' < {} < '{}'".format(str(start), str(header), str(end))
    return df.query(qstr)


def load_data(nrows):
    df = pd.read_csv(DATA_PATH, nrows=nrows, parse_dates=True,
                     infer_datetime_format=True, engine="c")
    return df
