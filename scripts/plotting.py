
import json
import shapely.geometry as geom
import common


def plot_manhattan(ax):
    nyc = common.get_nyc_geojson()
    manh = max(iter(nyc), key=lambda v: v.area)
    x, y = manh.exterior.xy
    ax.plot(x, y, "k-", linewidth=6)
