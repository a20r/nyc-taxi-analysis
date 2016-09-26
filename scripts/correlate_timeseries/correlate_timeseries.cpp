#include <fstream>
#include <vector>
#include <sstream>
#include <cmath>
#include <boost/progress.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <cnpy.h>


using namespace boost::posix_time;
using namespace std;

const string ts_dir = "data/ts/";
const int n_stations = 101;
const string dt_fmt = "%Y-%m-%d %H:%M:%S";
const int interval_size = 72;
const int n_bins = 60 * 24 / interval_size;

typedef vector<int> histogram_t;
typedef vector<vector<vector<string> *> *> pairwise_ts_t;
typedef vector<vector<vector<histogram_t> *> *> pairwise_histograms_t;


vector<histogram_t> *make_histograms()
{
    return new vector<histogram_t>(365, histogram_t(n_bins, 0));
}

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

pairwise_histograms_t *make_pairwise_histograms()
{
    pairwise_histograms_t *all_hists = new pairwise_histograms_t(n_stations);

    for (int i = 0; i < n_stations; i++)
    {
        for (int j = 0; j < n_stations; j++)
        {
            all_hists->at(i) = new vector<vector<histogram_t> *>(
                    n_stations);
        }
    }
    return all_hists;
}


inline string get_ts_fname(size_t p_st, size_t d_st)
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
    boost::progress_display show_progress(
            n_stations, cout, "\nLoading Timeseries\n", "", "");

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

template<typename T>
inline double mean(vector<T> nums)
{
    double m = 0.0;

    for (size_t i = 0; i < nums.size(); i++)
    {
        m += (double) nums[i] / nums.size();
    }

    return m;
}

template<typename T>
inline double variance(vector<T> x, double m)
{
    double s = 0.0;

    for (size_t i = 0; i < x.size(); i++)
    {
        s += powf(x[i] - m, 2);
    }

    return s / x.size();
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
    double left_den = sqrt(x.size() * variance(x, xm));
    double right_den = sqrt(x.size() * variance(y, ym));
    double p = num / (left_den * right_den);

    if (std::isnan(p)) {
        return 0;
    }

    return p;
}

void construct_histograms(vector<string> *ts, vector<histogram_t> *hists)
{
    for (size_t i = 0; i < ts->size(); i++)
    {
        tm t = to_tm(time_from_string(ts->at(i)));
        int bin = (t.tm_hour * 60 + t.tm_min) / interval_size;
        hists->at(t.tm_yday)[bin]++;
    }
}

void construct_all_histograms(pairwise_ts_t *all_ts,
        pairwise_histograms_t *all_hists)
{
    boost::progress_display show_progress(
            n_stations, cout, "\nConstructing Histograms\n", "", "");

    #pragma omp parallel for
    for (int i = 0; i < n_stations; i++)
    {
        for (int j = 0; j < n_stations; j++)
        {
            vector<histogram_t> *hists = make_histograms();
            construct_histograms(all_ts->at(i)->at(j), hists);
            all_hists->at(i)->at(j) = hists;
        }

        ++show_progress;
    }
}

void compute_all_correlations(pairwise_histograms_t *all_hists,
        double *mean_cors, double *stds)
{
    boost::progress_display show_progress(
            n_stations, cout, "\nComputing Correlations\n", "", "");

    #pragma omp parallel for
    for (int p0 = 0; p0 < n_stations; p0++)
    {
        for (int d0 = 0; d0 < n_stations; d0++)
        {
            for (int p1 = 0; p1 < n_stations; p1++)
            {
                for (int d1 = 0; d1 < n_stations; d1++)
                {
                    vector<double> cors;
                    for (int day = 0; day < 365; day++)
                    {
                        histogram_t t0 = all_hists->at(p0)->at(d0)->at(day);
                        histogram_t t1 = all_hists->at(p1)->at(d1)->at(day);
                        double cor = pearson(t0, t1);
                        cors.push_back(cor);
                    }

                    int index = p0 * pow(n_stations, 3)
                        + d0 * pow(n_stations, 2) + p1 * n_stations + d1;
                    double mean_cor = mean(cors);
                    mean_cors[index] = mean_cor;
                    stds[index] = sqrt(variance(cors, mean_cor));
                }
            }
        }

        ++show_progress;
    }
}

void save_matrix(double *arr, string fname)
{
    cout << "\nWriting to " << fname << endl;
    const unsigned int shape[] = {n_stations, n_stations, n_stations,
        n_stations};
    cnpy::npy_save(fname, arr, shape, 4, "w");
}

int main()
{
    // Loading timeseries data
    pairwise_ts_t *all_ts = make_pairwise_ts();
    load_ts(all_ts);

    // Constructing histograms
    pairwise_histograms_t *all_hists = make_pairwise_histograms();
    construct_all_histograms(all_ts, all_hists);

    // Computing correlations
    size_t arr_size = pow(n_stations, 4);
    double *mean_cors = new double[arr_size];
    double *stds = new double[arr_size];
    compute_all_correlations(all_hists, mean_cors, stds);
    save_matrix(mean_cors, "data/mean_cors.npy");
    save_matrix(stds, "data/stds.npy");

    return 0;
}
