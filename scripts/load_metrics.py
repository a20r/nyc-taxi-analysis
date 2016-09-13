#! /usr/bin/python

import time
import warnings
import tqdm
import glob
import io
import common
import os
import os.path
import numpy as np
import pandas
import re
from cStringIO import StringIO
from collections import defaultdict
from datetime import datetime
from progressbar import ProgressBar, ETA, Percentage, Bar
from itertools import product
from multiprocessing import Pool
from pprint import pprint


SHOW_IND_PROGRESS = True
TIME_STEP = 30
GRAPHS_PREFIX = "graphs"
DATA_FILE_TEMPLATE = "data-{}-{}.txt"
REG = r"-?\d*\.\d+|-?\d+"
folder = "/home/wallar/nfs/data/data-sim/v1000-c10-w120-p0/"


vehicles = [1000, 2000, 3000]
caps = [2, 4]
days = [1, 2, 3]
waiting_times = [300]
predictions = [-1, 0, 200, 400, 600]
total = len(vehicles) * len(caps) * len(days) * len(waiting_times) \
    * len(predictions)


class PassengerData(object):
    def __init__(self, line):
        attrs = map(float, line)
        self.identity = attrs[0]
        self.origin = [attrs[2], attrs[1]]
        self.destination = [attrs[4], attrs[3]]
        self.station_origin = attrs[5]
        self.station_origin_coord = [attrs[7], attrs[6]]
        self.station_destination = attrs[8]
        self.station_destination_coord = [attrs[10], attrs[9]]
        self.time_req = attrs[11]
        self.time_pickup = attrs[12]
        self.time_dropoff = attrs[13]
        self.travel_time_optim = int(attrs[14])
        self.vehicle_pickup = attrs[15]


class PerformanceData(object):
    def __init__(self, line):
        attrs = map(float, line)
        self.n_pickups = attrs[0]
        self.total_pickups = attrs[1]
        self.n_dropoffs = attrs[2]
        self.total_dropoffs = attrs[3]
        self.n_ignored = attrs[4]
        self.total_ignored = attrs[5]


class FolderInfo(object):
    def __init__(self, folder_name):
        nums = map(int, re.findall("\d+", folder_name))
        self.nums = nums
        self.n_vehicles = nums[0]
        self.max_capacity = nums[1]
        self.max_waiting_time = nums[2]
        self.predictions = nums[3]
        self.contains_date = False
        if len(nums) > 4:
            self.weekday = nums[4]
            self.week = nums[5]
            self.year = nums[6]
            self.timestamp = nums[7]
            self.contains_date = True

    def get_start_date(self):
        if self.contains_date:
            strt = "{}-{}-{}".format(self.weekday - 1, self.week, self.year)
            dt = datetime.strptime(strt, "%w-%U-%Y")
            return dt
        else:
            raise ValueError("Folder does not contain date")

    def to_dict(self):
        data = dict()
        data["n_vehicles"] = self.n_vehicles
        data["capacity"] = self.max_capacity
        data["waiting_time"] = self.max_waiting_time
        data["predictions"] = self.predictions
        return data

    def to_json(self):
        t = "[n_vehicles: {}, capacity: {}, waiting_time: {}, predictions: {}]"
        return t.format(*self.nums)

    def __str__(self):
        t = "(n_vehicles: {}, capacity: {}, waiting_time: {}, predictions: {})"
        return t.format(*self.nums)

    def __repr__(self):
        return "FolderInfo({})".format(", ".join(str(n) for n in self.nums))


def get_subdirs(a_dir):
        return [name for name in os.listdir(a_dir)
                if os.path.isdir(os.path.join(a_dir, name))]


def get_empty_type(line):
    line_sep = line.split("%")
    passes = re.findall(r"-?\d+", line_sep[1])
    reqs = re.findall(r"-?\d+", line_sep[2])
    is_rb = int(line_sep[-1]) == 1
    if is_rb:
        return "empty_rebalancing"
    if len(passes) == 0 and len(reqs) > 0 and not is_rb:
        return "empty_moving_to_pickup"
    if len(passes) == 0 and len(reqs) == 0 and not is_rb:
        return "empty_waiting"
    else:
        return "not_empty"


def process_vehicles(fin, data, n_vecs, cap, rebalancing, is_long,
                     trip_of_pass_shared):
    while True:
        line = fin.readline()
        if "Vehicles" in line:
            break
    ppv = list()
    km_travelled = list()
    line = fin.readline()
    active_taxis = 0.0
    taxi_pass_count = defaultdict(int)
    empty_types = defaultdict(int)
    passes_list = list()
    n_shared = 0
    n_shared_overall = 0
    counter = 0
    ets = ["empty_rebalancing", "empty_moving_to_pickup",
           "empty_waiting", "not_empty"]

    while len(line) > 1:
        passes = re.findall(r"-?\d+", line.split("%")[1])
        passes = map(int, passes)
        passes_list.append(passes)
        ppv.append(len(passes))
        km = float(line.split("%")[5])
        km_travelled.append(km)
        active_taxis += 1 if len(passes) > 0 else 0
        taxi_pass_count["time_pass_{}".format(len(passes))] += 1
        empty_type = get_empty_type(line)
        empty_types[empty_type] += 1
        if len(passes) == 1:
            # Check if it was shared before
            if trip_of_pass_shared[passes[0]] == 1:
                n_shared_overall += 1
        elif len(passes) > 1:
            # They are sharing
            for i in [0, len(passes) - 1]:
                n_shared_overall += 1
                if trip_of_pass_shared[passes[i]] == 0:
                    n_shared += 1
                    trip_of_pass_shared[passes[i]] = 1
        line = fin.readline()
        counter += 1

    data["mean_passengers"].append(np.mean(ppv))
    data["med_passengers"].append(np.median(ppv))
    data["std_passengers"].append(np.std(ppv))
    data["active_taxis"].append(active_taxis)
    data["mean_km_travelled"].append(np.mean(km_travelled))
    data["std_km_travelled"].append(np.std(km_travelled))
    data["total_km_travelled"].append(sum(km_travelled))
    data["n_vehicles"].append(n_vecs)
    data["capacity"].append(cap)
    data["rebalancing"].append(rebalancing)
    data["is_long"].append(is_long)
    data["n_shared"].append(n_shared)
    data["n_shared_overall"].append(n_shared_overall)

    for i in xrange(11):
        key = "time_pass_{}".format(i)
        data[key].append(taxi_pass_count[key])
    for et in ets:
        data[et].append(empty_types[et])

    return trip_of_pass_shared


def move_to_passengers(fin, data):
    while True:
        line = fin.readline()
        if "Passengers" in line:
            n_pass = int(re.findall(r"\d+", line)[0])
            data["total_passengers"].append(n_pass)
            return


def process_passengers(fin, data):
    l = fin.readline()
    line = re.findall(REG, l)
    if len(line) > 0:
        waiting_time = list()
        delay = list()
        while len(line) > 0:
            pd = PassengerData(line)
            if pd.time_dropoff > 0:
                waiting_time.append(pd.time_pickup - pd.time_req)
                dly = pd.time_dropoff - pd.time_req - pd.travel_time_optim
                delay.append(dly)
            l = fin.readline()
            line = re.findall(REG, l)
        data["mean_waiting_time"].append(np.mean(waiting_time))
        data["med_waiting_time"].append(np.median(waiting_time))
        data["std_waiting_time"].append(np.std(waiting_time))
        data["mean_delay"].append(np.mean(delay))
        data["med_delay"].append(np.median(delay))
        data["std_delay"].append(np.std(delay))
    else:
        data["mean_waiting_time"].append(0)
        data["med_waiting_time"].append(0)
        data["std_waiting_time"].append(0)
        data["mean_delay"].append(0)
        data["med_delay"].append(0)
        data["std_delay"].append(0)


def process_performance(fin, data):
    fin.readline()
    line = re.findall(REG, fin.readline())
    pd = PerformanceData(line)
    data["n_pickups"].append(pd.n_pickups)
    data["n_dropoffs"].append(pd.n_dropoffs)
    data["n_ignored"].append(pd.n_ignored)


def process_requests(fin, data):
    fin.readline()
    fin.readline()
    l = fin.readline()
    n_reqs_assigned = 0
    n_reqs_unassigned = 0
    while len(l) > 1:
        assigned = re.findall(r"[-+]?\d*\.\d+|\d+", l)[11]
        if assigned > 0:
            n_reqs_assigned += 1
        else:
            n_reqs_unassigned += 1
        l = fin.readline()
    data["n_reqs_assigned"].append(n_reqs_assigned)
    data["n_reqs_unassigned"].append(n_reqs_unassigned)
    data["n_reqs"].append(n_reqs_assigned + n_reqs_unassigned)


def convert_to_dataframe(data, folder_info, is_long=0):
    freq = "30S"
    start = folder_info.get_start_date()
    if is_long == 0:
        periods = common.MAX_SECONDS / TIME_STEP
    else:
        periods = len(data["is_long"])
    inds = pandas.date_range(start=start, periods=periods, freq=freq)
    for k in data.keys():
        data[k] = np.array(data[k])
    data["capacity"] = np.array(data["capacity"], dtype=int)
    data["n_vehicles"] = np.array(data["n_vehicles"], dtype=int)
    data["time"] = inds
    return pandas.DataFrame(data)


def extract_metrics(folder, n_vecs, cap, rebalancing, is_long):
    folder_info = FolderInfo(folder.split("/")[-2])
    g_folder = folder + GRAPHS_PREFIX + "/"
    data = defaultdict(list)
    if is_long == 0:
        fl = common.MAX_SECONDS / TIME_STEP
    else:
        fl = len(os.listdir(g_folder))
    if SHOW_IND_PROGRESS:
        preface = "Extracting Metrics (" + g_folder + "): "
        widgets = [preface, Bar(), Percentage(), "| ", ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=fl).start()
        pbar = tqdm.tqdm(total=fl, desc=preface, position=0)
    trip_of_pass_shared = [0] * 1000000
    for i in xrange(fl):
        try:
            # t = i * TIME_STEP + 1800
            t = i * TIME_STEP
            filename = g_folder + DATA_FILE_TEMPLATE.format(GRAPHS_PREFIX, t)
            with open(filename, "rb") as fstream:
                fin = StringIO(fstream.read())
                process_requests(fin, data)
                trip_of_pass_shared = process_vehicles(
                    fin, data, n_vecs, cap, rebalancing, is_long,
                    trip_of_pass_shared)
                move_to_passengers(fin, data)
                process_passengers(fin, data)
                process_performance(fin, data)
            if SHOW_IND_PROGRESS:
                pbar.update(1)
        except IOError:
            pass
    if SHOW_IND_PROGRESS:
        pbar.close()
    return convert_to_dataframe(data, folder_info, is_long)


def load_parameters(param_file):
    params = dict()
    with io.open(param_file, "rb") as fin:
        for line in fin:
            vs = line.split(":")
            key = vs[0]
            values = re.findall(REG, vs[1])
            if len(values) > 0:
                params[key] = float(values[0])
            else:
                params[key] = vs[1].strip()
        return params


def extract_dataframe_worker(folders):
    subdir = folders[0] + "/" + folders[1] + "/"
    params = load_parameters(subdir + "parameters.txt")
    n_vehicles = params["NUMBER_VEHICLES"]
    cap = params["maxPassengersVehicle"]
    rebalancing = params["USE_REBALANCING"]
    df = extract_metrics(subdir, n_vehicles, cap, rebalancing, 1)
    return df


def extract_dataframe(folder):
    dirs = get_subdirs(folder)
    dfs = list()
    for dr in dirs:
        subdir = folder + "/" + dr + "/"
        params = load_parameters(subdir + "parameters.txt")
        n_vehicles = params["NUMBER_VEHICLES"]
        cap = params["maxPassengersVehicle"]
        rebalancing = params["USE_REBALANCING"]
        df = extract_metrics(subdir, n_vehicles, cap, rebalancing, 1)
        dfs.append(df)
    return pandas.concat(dfs)


def extract_dataframe_subdir(dr):
    try:
        subdir = dr + "/"
        params = load_parameters(subdir + "parameters.txt")
        n_vehicles = params["NUMBER_VEHICLES"]
        cap = params["maxPassengersVehicle"]
        rebalancing = params["USE_REBALANCING"]
        df = extract_metrics(subdir, n_vehicles, cap, rebalancing, 1)
        df.to_csv(subdir + "metrics_icra.csv")
        return df
    except:
        print "error:", dr


def extract_new_dataframes(dirs):
    # pool = Pool(8)
    # pool.map(extract_dataframe_subdir, dirs)
    # pool.close()
    for dr in dirs:
        extract_dataframe_subdir(dr)


def get_ready_folders(folder):
    ret_dirs = list()
    dirs = get_subdirs(folder)
    for dr in dirs:
        l = len(dr.split("-"))
        if l == 4 or l == 5:
            ret_dirs.append(dr)
    return ret_dirs


def extract_all_dataframes(folder):
    data_dirs = get_ready_folders(folder)
    preface = "Extracting Metrics"
    widgets = [preface, Bar(), Percentage(), "| ", ETA()]
    pbar = ProgressBar(widgets=widgets, maxval=len(data_dirs)).start()
    counter = 1
    print data_dirs
    exit()
    for data_folder in data_dirs:
        pool = Pool(8)
        dirs = get_subdirs(folder + data_folder)
        folder_l = [folder + data_folder] * len(dirs)
        folders = zip(folder_l, dirs)
        dfs = list()
        print map(lambda v: v[1].split("-")[4], folders)
        continue
        for wdf in pool.imap(extract_dataframe_worker, folders):
            dfs.append(wdf)
        df = pandas.concat(dfs)
        df.to_csv(folder + data_folder + "/metrics_pnas_2.csv")
        pbar.update(counter)
        counter += 1
        pool.close()
    pbar.finish()


def get_dirs_to_process():
    prod = product(vehicles, caps, waiting_times, predictions, days)
    baddies = list()
    for v, c, wt, p, d in tqdm.tqdm(prod, total=total):
        try:
            df = common.get_metrics_day(v, c, wt, p, d)
            if df.shape[0] < 2879:
                baddies.append(common.get_metric_folder(v, c, wt, p, d))
        except IOError:
            baddies.append(common.get_metric_folder(v, c, wt, p, d))
        except ValueError:
            pass
    return baddies


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    NFS_PATH = "/data/drl/mod_sim_data/data-sim/"
    dirs = get_dirs_to_process()
    pprint(dirs)
    # dirs = glob.glob(NFS_PATH + "*p[2|4|6]00*2013*")
    extract_new_dataframes(dirs)
