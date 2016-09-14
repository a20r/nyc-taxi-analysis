
#include <fstream>
#include <vector>
#include <sstream>
#include <boost/progress.hpp>

using namespace std;

const string fname = "/home/wallar/fast_data/nyc_taxi_data.csv";

void parse_line(string, line, string &p_dt, double &p_lng, double &p_lat,
        double &d_lng, double &d_lat)
{
    stringstream line_stream(line);
    string cell;
    int counter = 0;
    while (getline(line_stream, cell, ','))
    {
        switch (counter++)
        {
            case 1: p_dts.push_back(cell);
            case 5: p_lngs.push_back(stof(cell));
            case 6: p_lats.push_back(stof(cell));
            case 8: d_lngs.push_back(stof(cell));
            case 9: d_lats.push_back(stof(cell));
        }
    }
}

int main()
{
    ifstream file(fname, ios::binary | ios::ate);
    int num_rows = 165114362;
    vector<string> p_dts;
    vector<double> p_lngs, p_lats, d_lngs, d_lats;

    boost::progress_display show_progress(num_rows);
    #pragma omp parallel for
    for (int i = 0; i < num_rows; i++)
    {
        string line;
        getline(file, line);

        if (i > 0)
        {
            string p_dt;
            double p_lng, p_lat, d_lng, d_lat;
            parse_line(line, p_dt, p_lng, p_lat, d_lng, d_lat);
        }

        ++show_progress;
    }
}
