
import common
import util
from sklearn.cluster import KMeans


#@util.profile()
def cluster_pickups(df, **kwargs):
    pickups = common.get_pickup_geos(df)
    ap = KMeans(**kwargs)
    ap.fit(pickups)
    return ap


#@util.profile()
def cluster_dropoffs(df, **kwargs):
    dropoffs = common.get_dropoff_geos(df)
    ap = KMeans(**kwargs)
    ap.fit(dropoffs)
    return ap
