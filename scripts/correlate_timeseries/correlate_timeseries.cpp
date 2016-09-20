#include <fstream>
#include <vector>
#include <sstream>
#include <cmath>
#include <boost/progress.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>


using namespace boost::posix_time;
using namespace std;

const string ts_dir = "data/ts/";
const int n_stations = 101;
const string dt_fmt = "%Y-%m-%d %H:%M:%S";
const int interval_size = 72;
const int n_bins = 60 * 24 / interval_size;

typedef vector<vector<vector<string> *> *> pairwise_ts_t;
typedef vector<int> histogram_t;
typedef vector<histogram_t> histograms_t;

pairwise_ts_t *make_pairwise_ts()
{
    pairwise_ts_t *all_ts = new pairwise_ts_t(n_stations);

    for (int i = 0; i < n_stations; i++)
    {
        for (int j = 0; j < n_stations; j++)
        {
            all_ts->at(i) = new vector<vector<string> *>(n_stations);
        }
    }
    return all_ts;
}

string get_ts_fname(size_t p_st, size_t d_st)
{
    ostringstream os;
    os << ts_dir << p_st << "-" << d_st << ".txt";
    return os.str();
}

bool load_ts(size_t p_st, size_t d_st, vector<string> *ts)
{
    string fname = get_ts_fname(p_st, d_st);
    ifstream file(fname);
    string line;

    while (getline(file, line))
    {
        ts->push_back(line);
    }

    return true;
}

bool load_ts(pairwise_ts_t *all_ts)
{
    boost::progress_display show_progress(n_stations);

    #pragma omp parallel for
    for (int i = 0; i < n_stations; i++)
    {
        for (int j = 0; j < n_stations; j++)
        {
            vector<string> *ts = new vector<string>;
            load_ts(i, j, ts);
            all_ts->at(i)->at(j) = ts;
        }

        ++show_progress;
    }

    return true;
}

int to_mins_in_day(string dt)
{
    tm t = to_tm(time_from_string(dt));
    return t.tm_hour * 60 + t.tm_min;
}

inline double mean(vector<int> nums)
{
    double m = 0.0;

    for (size_t i = 0; i < nums.size(); i++)
    {
        m += (double) nums[i] / nums.size();
    }

    return m;
}

inline double std_sq(vector<int> x, double m)
{
    double s = 0.0;

    for (size_t i = 0; i < x.size(); i++)
    {
        s += powf(x[i] - m, 2);
    }

    return s;
}

inline double std_mult(vector<int> x, vector<int> y, double xm, double ym)
{
    double s = 0.0;

    for (size_t i = 0; i < x.size(); i++)
    {
        s += (x[i] - xm) * (y[i] - ym);
    }

    return s;
}

inline double pearson(vector<int> x, vector<int> y)
{
    double xm = mean(x), ym = mean(y);
    double num = std_mult(x, y, xm, ym);
    double den = sqrt(std_sq(x, xm)) * sqrt(std_sq(y, ym));
    return num / den;
}

void construct_histograms(vector<string> *ts, vector<histogram_t> &hists)
{
    hists = vector<histogram_t>(365, histogram_t(n_bins, 0));
    for (size_t i = 0; i < ts->size(); i++)
    {
        tm t = to_tm(time_from_string(ts->at(i)));
        int bin = (t.tm_hour * 60 + t.tm_min) / interval_size;
        hists[t.tm_yday][bin]++;
    }
}

int main()
{
    pairwise_ts_t *all_ts = make_pairwise_ts();
    load_ts(all_ts);
    vector<histogram_t> h1;
    construct_histograms(all_ts->at(42)->at(22), h1);
    vector<histogram_t> h2;
    construct_histograms(all_ts->at(12)->at(42), h2);
    cout << pearson(h1[2], h2[2]) << endl;
    return 0;
}
