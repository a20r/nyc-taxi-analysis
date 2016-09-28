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

typedef vector<double> histogram_t;
// typedef vector<vector<vector<string> *> *> pairwise_ts_t;
// typedef vector<vector<vector<int> *> *> pairwise_duration_t;
typedef vector<vector<vector<histogram_t> *> *> pairwise_histograms_t;

template<typename T>
using pairwise_ts_t = vector<vector<vector<T> *> *>;

vector<histogram_t> *make_histograms()
{
    return new vector<histogram_t>(365, histogram_t(n_bins, 0));
}

template<typename T>
pairwise_ts_t<T> *make_pairwise_ts()
{
    pairwise_ts_t<T> *all_ts = new pairwise_ts_t<T>(n_stations);

    for (int i = 0; i < n_stations; i++)
    {
        for (int j = 0; j < n_stations; j++)
        {
            all_ts->at(i) = new vector<vector<T> *>(n_stations);
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

bool load_ts(size_t p_st, size_t d_st, vector<string> *times,
        vector<int> *durs)
{
    string fname = get_ts_fname(p_st, d_st);
    ifstream file(fname);
    string line, cell;
    while (getline(file, line))
    {
        stringstream line_stream(line);
        getline(line_stream, cell, ',');
        times->push_back(cell);
        getline(line_stream, cell, ',');
        durs->push_back(stoi(cell));
    }

    return true;
}

bool load_ts(pairwise_ts_t<string> *all_ts, pairwise_ts_t<int> *all_durs)
{
    boost::progress_display show_progress(
            n_stations, cout, "\nLoading Timeseries\n", "", "");

    #pragma omp parallel for
    for (int i = 0; i < n_stations; i++)
    {
        for (int j = 0; j < n_stations; j++)
        {
            vector<string> *times = new vector<string>;
            vector<int> *durs = new vector<int>;
            load_ts(i, j, times, durs);
            all_ts->at(i)->at(j) = times;
            all_durs->at(i)->at(j) = durs;
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

template<typename T>
inline double std_mult(vector<T> x, vector<T> y, double xm, double ym)
{
    double s = 0.0;

    for (size_t i = 0; i < x.size(); i++)
    {
        s += (x[i] - xm) * (y[i] - ym);
    }

    return s;
}

template<typename T>
inline double pearson(vector<T> x, vector<T> y)
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

void construct_histograms(vector<string> *times, vector<int> *durs,
        vector<histogram_t> *times_hists,
        vector<histogram_t> *durs_hists)
{
    for (size_t i = 0; i < times->size(); i++)
    {
        tm t = to_tm(time_from_string(times->at(i)));
        int bin = (t.tm_hour * 60 + t.tm_min) / interval_size;
        times_hists->at(t.tm_yday)[bin]++;
        durs_hists->at(t.tm_yday)[bin] += durs->at(i);
    }

    for (size_t i = 0; i < 365; i++)
    {
        for (size_t j = 0; j < n_bins; j++)
        {
            durs_hists->at(i)[j] = durs_hists->at(i)[j]
                / times_hists->at(i)[j];
        }
    }
}

void construct_all_histograms(pairwise_ts_t<string> *all_ts,
        pairwise_ts_t<int> *all_durs,
        pairwise_histograms_t *times_hists,
        pairwise_histograms_t *durs_hists)
{
    boost::progress_display show_progress(
            n_stations, cout, "\nConstructing Histograms\n", "", "");

    #pragma omp parallel for
    for (int i = 0; i < n_stations; i++)
    {
        for (int j = 0; j < n_stations; j++)
        {
            vector<histogram_t> *times_hist = make_histograms();
            vector<histogram_t> *durs_hist = make_histograms();
            construct_histograms(all_ts->at(i)->at(j), all_durs->at(i)->at(j),
                    times_hist, durs_hist);
            times_hists->at(i)->at(j) = times_hist;
            durs_hists->at(i)->at(j) = durs_hist;
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
    pairwise_ts_t<string> *all_ts = make_pairwise_ts<string>();
    pairwise_ts_t<int> *all_durs = make_pairwise_ts<int>();
    load_ts(all_ts, all_durs);

    // Constructing histograms
    pairwise_histograms_t *times_hists = make_pairwise_histograms();
    pairwise_histograms_t *durs_hists = make_pairwise_histograms();
    construct_all_histograms(all_ts, all_durs, times_hists, durs_hists);

    // Computing correlations
    size_t arr_size = pow(n_stations, 4);
    double *mean_cors = new double[arr_size];
    double *stds = new double[arr_size];
    compute_all_correlations(times_hists, mean_cors, stds);
    save_matrix(mean_cors, "data/mean_cors.npy");
    save_matrix(stds, "data/stds.npy");

    // Computing correlations
    compute_all_correlations(durs_hists, mean_cors, stds);
    save_matrix(mean_cors, "data/durs_mean_cors.npy");
    save_matrix(stds, "data/durs_stds.npy");

    return 0;
}
