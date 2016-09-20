#include <fstream>
#include <vector>
#include <sstream>
#include <cmath>
#include <boost/progress.hpp>

using namespace std;

const string ts_dir = "data/ts/";
const int n_stations = 101;

typedef vector<vector<vector<string> *> *> pairwise_ts_t;

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

int main()
{
    pairwise_ts_t *all_ts = make_pairwise_ts();
    load_ts(all_ts);
    cout << all_ts->at(42)->at(42)->size() << endl;
    return 0;
}
