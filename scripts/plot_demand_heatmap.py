
import common
import folium
from datetime import datetime
from folium import plugins


def generate_demand_heatmap():
    df = common.load_data(nrows=10000000)
    start_dt = datetime(2014, 1, 10, 1, 0)
    end_dt = datetime(2014, 1, 10, 2, 0)
    df = common.query_dates(df, start_dt, end_dt, "dropoff_datetime")
    arr = common.get_dropoff_geos(df)
    hmap = folium.Map(location=[40.760096, -73.978844], zoom_start=12)
    hm = plugins.HeatMap(arr)
    hmap.add_children(hm)
    return hmap


if __name__ == "__main__":
    hmap = generate_demand_heatmap()
    hmap.save("/home/wallar/www/hmap.html")
