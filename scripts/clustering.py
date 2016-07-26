
import common
import util
import folium
from folium import plugins
from sklearn.cluster import DBSCAN


@util.profile()
def cluster_pickups(df):
    pickups = common.get_dropoff_geos(df)
    ap = DBSCAN(eps=0.0005)
    ap.fit(pickups)
    return ap


if __name__ == "__main__":
    df = common.load_data(nrows=2000)
    ap = cluster_pickups(df)
    arr = common.get_dropoff_geos(df)
    hmap = folium.Map(location=[40.760096, -73.978844], zoom_start=12)
    hm = plugins.HeatMap(arr)
    hmap.add_children(hm)
    for cc in ap.components_:
        folium.Marker(cc).add_to(hmap)
    hmap.save("/home/wallar/www/hmap.html")
