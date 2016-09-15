
#include <fstream>
#include <vector>
#include <sstream>
#include <cmath>
#include <boost/progress.hpp>
#include <nanoflann.hpp>

using namespace std;
using namespace nanoflann;

const string data_fname = "/home/wallar/fast_data/nyc_taxi_data.csv";
const string stations_fname = "data/stations.csv";
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
        std::vector<GeoPoint>  pts;

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

bool parse_data_line(string line, string &p_dt, double &p_lng, double &p_lat,
        double &d_lng, double &d_lat)
{
    stringstream line_stream(line);
    string cell;
    int counter = 0;
    while (getline(line_stream, cell, ','))
    {
        if (cell.size() == 0)
        {
            return false;
        }

        try {
            switch (counter++)
            {
                case 1: p_dt = cell;
                case 5: p_lng = stof(cell);
                case 6: p_lat = stof(cell);
                case 9: d_lng = stof(cell);
                case 10: d_lat = stof(cell);
            }
        }
        catch (const invalid_argument &ia)
        {
            cout << line << endl << endl;
            return false;
        }
    }

    return true;
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
            case 1: lng = stof(cell);
            case 2: lat = stof(cell);
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

void associate_stations(kd_tree_t &index)
{
    ifstream file(data_fname);
    string l;
    getline(file, l);

    boost::progress_display show_progress(num_rows);

    #pragma omp parallel for
    for (int i = 0; i < num_rows; i++)
    {
        string line;
        #pragma omp critical
        getline(file, line);

        string p_dt;
        double p_lng, p_lat, d_lng, d_lat;
        bool worked = parse_data_line(line, p_dt, p_lng,
                p_lat, d_lng, d_lat);
        if (worked)
        {
            size_t ret_index;
            double out_dist_sqr;
            KNNResultSet<double> resultSet(1);
            resultSet.init(&ret_index, &out_dist_sqr);
            double query_pt[2] = {p_lng, p_lat};
            index.findNeighbors(resultSet, &query_pt[0], SearchParams(10));
        }

        ++show_progress;
    }
}

int main()
{
    GeoPoints gps = load_stations();
    kd_tree_t index(2, gps, KDTreeSingleIndexAdaptorParams(10));
    index.buildIndex();
    associate_stations(index);
}
