
import json
import shapely.geometry as geom


def plot_manhattan(ax):
    with open("../sandbox/nyc.geo.json") as f:
        nyc_dict = json.loads(f.read())
        nyc = geom.shape(nyc_dict["geometry"])
        manh = max(iter(nyc), key=lambda v: v.area)
        x, y = manh.exterior.xy
        ax.plot(x, y, "k-", linewidth=6)
