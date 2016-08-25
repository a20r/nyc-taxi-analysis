
import common


def find_clusters(geos, constructor, **kwargs):
    cl = constructor(**kwargs)
    cl.fit(geos)
    return cl


#@util.profile()
def cluster_pickups(df, constructor ,**kwargs):
    pickups = common.get_pickup_geos(df)
    return find_clusters(pickups, constructor, **kwargs)


#@util.profile()
def cluster_dropoffs(df, constructor, **kwargs):
    dropoffs = common.get_dropoff_geos(df)
    return find_clusters(dropoffs, constructor, **kwargs)
