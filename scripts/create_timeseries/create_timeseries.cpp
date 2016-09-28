
#include <fstream>
#include <vector>
#include <sstream>
#include <cmath>
#include <nanoflann.hpp>
#include <boost/progress.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>

using namespace boost::posix_time;
using namespace std;
using namespace nanoflann;

const string data_fname = "/home/wallar/fast_data/nyc_taxi_data.csv";
const string stations_fname = "data/stations.csv";
const string ts_dir = "data/ts/";
const int num_rows = 165114362;
const double earth_radius = 6371;

class GeoPoint
{
    public:
        double  lng, lat;
        GeoPoint(double lng, double lat) : lng(lng), lat(lat) {}
};

class GeoPoints
{
    public:
        std::vector<GeoPoint> pts;

        inline size_t kdtree_get_point_count() const
        {
            return pts.size();
        }

        inline double kdtree_distance(const double *p1, const size_t idx_p2,
                size_t) const
        {
            double lat1 = p1[1] * (M_PI / 180.0);
            double lng1 = p1[0] * (M_PI / 180.0);
            double lat2 = pts[idx_p2].lat * (M_PI / 180.0);
            double lng2 = pts[idx_p2].lng * (M_PI / 180.0);
            double dlng = lng2 - lng1;
            double dlat = lat2 - lat1;
            double a = pow(sin(dlat / 2.0), 2) + cos(lat1) * cos(lat2)
                * pow(sin(dlng / 2.0), 2);
            double c = 2 * asin(sqrt(a));
            double dist_km = earth_radius * c;
            return dist_km;
        }

        inline double kdtree_get_pt(const size_t idx, int dim) const
        {
            if (dim <= 0)
            {
                return pts[idx].lng;
            } else {
                return pts[idx].lat;
            }
        }

        template <class BBOX>
        bool kdtree_get_bbox(BBOX& /* bb */) const { return false; }
};

typedef KDTreeSingleIndexAdaptor<
    L2_Simple_Adaptor<double, GeoPoints>,
    GeoPoints, 2> kd_tree_t;

bool parse_data_line(string line, string &p_dt, string &d_dt,
        double &p_lng, double &p_lat,
        double &d_lng, double &d_lat)
{
    stringstream line_stream(line);
    string cell;
    int counter = 0;
    while (getline(line_stream, cell, ','))
    {
        try {
            switch (counter++)
            {
                case 1: p_dt = cell;
                case 2: d_dt = cell;
                case 5: p_lng = stod(cell);
                case 6: p_lat = stod(cell);
                case 9: d_lng = stod(cell);
                case 10: d_lat = stod(cell);
            }
        }
        catch (const invalid_argument &ia)
        {
            return false;
        }
    }

    return !(p_lng == 0 or p_lat == 0 or d_lng == 0 or d_lat == 0);
}

bool parse_stations_line(string line, double &lng, double &lat)
{
    stringstream line_stream(line);
    string cell;
    int counter = 0;
    while (getline(line_stream, cell, ','))
    {
        switch (counter++)
        {
            case 1: lng = stod(cell);
            case 2: lat = stod(cell);
        }
    }

    return true;
}

GeoPoints load_stations()
{
    GeoPoints gps;
    ifstream file(stations_fname);

    string line;
    for (int i = 0; getline(file, line); i++)
    {
        if (i > 0)
        {
            double lng, lat;
            parse_stations_line(line, lng, lat);
            gps.pts.push_back(GeoPoint(lng, lat));
        }
    }
    return gps;
}

size_t get_nearest(kd_tree_t &index, double lng, double lat)
{
    size_t ret_index;
    double out_dist_sqr;
    KNNResultSet<double> resultSet(1);
    resultSet.init(&ret_index, &out_dist_sqr);
    double query_pt[2] = {lng, lat};
    index.findNeighbors(resultSet, &query_pt[0], SearchParams(10));
    return ret_index;
}

string get_ts_fname(size_t p_st, size_t d_st)
{
    ostringstream os;
    os << ts_dir << p_st << "-" << d_st << ".txt";
    return os.str();
}

void write_dt(size_t p_st, size_t d_st, string p_dt, time_duration dur)
{
    ofstream fout;
    fout.open(get_ts_fname(p_st, d_st), ios_base::app);
    #pragma omp critical
    fout << p_dt << "," << dur.total_seconds() << endl;
    fout.close();
}

void create_timeseries(kd_tree_t &index)
{
    ifstream file(data_fname);
    string l;
    getline(file, l);
    boost::progress_display show_progress(num_rows);

    #pragma omp parallel for
    for (int i = 2; i < num_rows; i++)
    {
        string line;
        #pragma omp critical
        getline(file, line);

        string p_dt, d_dt;
        double p_lng, p_lat, d_lng, d_lat;
        if (parse_data_line(line, p_dt, d_dt, p_lng, p_lat, d_lng, d_lat))
        {
            size_t p_st = get_nearest(index, p_lng, p_lat);
            size_t d_st = get_nearest(index, d_lng, d_lat);
            ptime pt = time_from_string(p_dt);
            ptime dt = time_from_string(d_dt);
            time_duration dur = dt - pt;
            write_dt(p_st, d_st, p_dt, dur);
        }
        ++show_progress;
    }
}

int main()
{
    GeoPoints gps = load_stations();
    cout << "Building tree" << endl;
    kd_tree_t index(2, gps, KDTreeSingleIndexAdaptorParams(1));
    index.buildIndex();
    cout << "Building timeseries" << endl;
    create_timeseries(index);
}
