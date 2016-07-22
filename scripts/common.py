
import pandas as pd
import os.path
import warnings
import logging
import time


DATA_DIR = "/media/wallar/storage/data/"
DATA_FILENAME = "nyc_taxi_data.csv.gz"
HDF5_FILENAME = "nyc_taxi_store.h5"
DATA_PATH = DATA_DIR + DATA_FILENAME
HDF5_PATH = DATA_DIR + HDF5_FILENAME


def profile(pargs=True):
    def dec(f):
        def __inner(*args, **kwargs):
            very_big = 1000
            print "Executing:", f.func_name
            if pargs:
                n_args = f.func_code.co_argcount
                print "With Args:",
                arg_str = str()
                for i, v in enumerate(f.func_code.co_varnames[:len(args)]):
                    astr = repr(args[i])
                    if len(astr) > very_big:
                        astr = type(args[i])
                    arg_str += "\n\t", v, ":", astr,
                if len(arg_str) == 0:
                    print "None"
                else:
                    print arg_str
                print "With Kwargs:",
                if len(kwargs.keys()) > 0:
                    print ""
                    for key in kwargs:
                        kwstr = repr(kwargs[key])
                        if len(kwstr) > very_big:
                            kwstr = type(kwargs[key])
                        print "\t", key, ":", kwstr
                else:
                    print "None"
            start = time.time()
            res = f(*args, **kwargs)
            end = time.time()
            print "Result:", repr(res) if len(repr(res)) < 1000 else type(res)
            print "Execution Duration:", end - start, "seconds"
            return res
        return __inner
    return dec


def timeit(func):
    def dec(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        print "Duration:", time.time() - start
        return res
    return dec


def get_dropoff_geos(df):
    return df.as_matrix(["dropoff_latitude", "dropoff_longitude"])


def get_pickup_geos(df):
    return df.as_matrix(["pickup_latitude", "pickup_longitude"])


def query_dates(df, start, end, header):
    qstr = "'{}' < {} < '{}'".format(str(start), str(header), str(end))
    return df.query(qstr)


@profile()
def load_data(nrows=None, load=False):
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
        logging.info("Writing to store")
        df.to_hdf(HDF5_PATH, "table", mode="w", append=False)
        return df
