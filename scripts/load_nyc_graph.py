
import networkx as nx
import tqdm
import pandas as pd
import numpy as np
import pickle
from common import NYC_DIR


def time_names(name):
    return ["id"] + [name + "_%d" % i for i in xrange(24)]


def load_nyc_graph():
    nyc_edges = pd.read_csv(NYC_DIR.format("edges"),
                            names=["id", "source", "sink"])
    nyc_nodes = pd.read_csv(NYC_DIR.format("points"),
                            names=["id", "lat", "lon"])
    nyc_week_times = pd.read_csv(NYC_DIR.format("week"),
                                 names=time_names("week"))
    # nyc_sat_times = pd.read_csv(NYC_DIR.format("sat"),
    #                             names=time_names("sat"))
    # nyc_sun_times = pd.read_csv(NYC_DIR.format("sun"),
    #                             names=time_names("sun"))
    nyc_graph = nx.DiGraph()
    n_edges = nyc_edges.shape[0]
    rng = tqdm.tqdm(
        nyc_edges.iterrows(), total=n_edges, ncols=100,
        desc="Loading NYC Graph")

    for i, edge in rng:
        src = edge["source"] - 1
        sink = edge["sink"] - 1
        src_pos = np.array([nyc_nodes.iloc[src]["lon"],
                            nyc_nodes.iloc[src]["lat"]])
        sink_pos = np.array([nyc_nodes.iloc[sink]["lon"],
                            nyc_nodes.iloc[sink]["lat"]])
        weights = nyc_week_times.iloc[i]
        nyc_graph.add_node(src, pos=src_pos)
        nyc_graph.add_node(sink, pos=sink_pos)
        nyc_graph.add_edge(edge["source"], edge["sink"], **weights)
    return nyc_graph


if __name__ == "__main__":
    nyc_graph = load_nyc_graph()
    with open("data/nyc-graph/nyc.pickle", "w") as fout:
        pickle.dump(nyc_graph, fout)
