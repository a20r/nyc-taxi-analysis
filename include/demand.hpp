
#ifndef DEMAND_HPP
#define DEMAND_HPP

#include <sstream>
#include <fstream>
#include <string>
#include <unordered_map>
#include <vector>
#include <functional>
#include <cmath>
#include <random>

using namespace std;

namespace mod
{

    const int interval_size = 60 * 15;

    class GeoLocation
    {
        public:
            double lat, lon;
            GeoLocation() {};
            ~GeoLocation() {};
            GeoLocation(double lat, double lon) : lat(lat), lon(lon)
            {
            };

            double distance(GeoLocation& gl)
            {
                double lat1 = lat;
                double lon1 = lon;
                double lat2 = gl.lat;
                double lon2 = gl.lon;
                lon1 = lon1 * (M_PI / 180.0);
                lat1 = lat1 * (M_PI / 180.0);
                lon2 = lon2 * (M_PI / 180.0);
                lat2 = lat2 * (M_PI / 180.0);
                double dlon = lon2 - lon1;
                double dlat = lat2 - lat1;
                double a = pow(sin(dlat / 2.0), 2) + cos(lat1) * cos(lat2)
                    * pow(sin(dlon / 2.0), 2);
                double c = 2 * asin(sqrt(a));
                double dist_km = 6367 * c;
                return dist_km;
            }
    };

    class Time
    {
        public:
            int day, secs;

            Time() {};
            ~Time() {};
            Time(int day, int secs) : day(day), secs(secs)
            {
            };

            int get_interval() const
            {
                return secs / interval_size;
            }
    };

    class Demand
    {
        public:
            int tau, day, pickup, dropoff;

            Demand() {};
            Demand(int tau, int day, int pickup, int dropoff) :
                tau(tau), day(day), pickup(pickup), dropoff(dropoff)
            {
            }
    };

    class DemandHash {
        public:
            size_t operator() (const Demand& demand) const
            {
                stringstream buffer;
                buffer << demand.tau << " ";
                buffer << demand.day << " ";
                buffer << demand.pickup << " ";
                buffer << demand.dropoff;
                return hash<string>()(buffer.str());
            }
    };

    inline bool operator== (Demand const& lhs, Demand const& rhs) {
        return lhs.tau == rhs.tau and lhs.day == rhs.day and
            lhs.pickup == rhs.pickup and lhs.dropoff == rhs.dropoff;
    };

    inline bool operator<= (Time const& lhs, Demand const& rhs) {
        if (lhs.day < rhs.day)
        {
            return true;
        }
        else if (lhs.day == rhs.day and lhs.get_interval() <= rhs.tau)
        {
            return true;
        }
        else
        {
            return false;
        }
    };

    inline bool operator>= (Time const& lhs, Demand const& rhs) {
        if (lhs.day > rhs.day)
        {
            return true;
        }
        else if (lhs.day == rhs.day and lhs.get_interval() >= rhs.tau)
        {
            return true;
        }
        else
        {
            return false;
        }
    };

    inline ostream& operator<< (ostream& os, const Demand& demand) {
        os << "Demand(";
        os << demand.tau << ", ";
        os << demand.day << ", ";
        os << demand.pickup << ", ";
        os << demand.dropoff;
        os << ")";
        return os;
    };

    inline ostream& operator<< (ostream& os, const Time& t) {
        os << "Time(" << t.day << ", " << t.secs << ")";
        return os;
    };

    class DemandLookup
    {
        private:
            unordered_map<Demand, double, DemandHash> demands;
            vector<Demand> demand_vec;
            vector<double> cum_sum;
            vector<GeoLocation> stations;
            vector<vector<double>> times;
            unordered_map<int, unordered_map<int, vector<int>>> paths;
            unordered_map<int, int> freqs;

        public:
            DemandLookup() {};
            ~DemandLookup() {};

            DemandLookup(string fn_stations, string fn_probs, string fn_times,
                    string fn_paths, string fn_freqs)
            {
                init(fn_stations, fn_probs, fn_times, fn_paths, fn_freqs);
            }

            void init(string fn_stations, string fn_probs, string fn_times,
                    string fn_paths, string fn_freqs)
            {
                cout << "Loading probabilities..." << endl;
                load_probs(fn_probs);
                cout << "Loading stations..." << endl;
                load_stations(fn_stations);
                cout << "Loading times..." << endl;
                load_times(fn_times);
                cout << "Loading paths..." << endl;
                load_paths(fn_paths);
                cout << "Loading frequencies..." << endl;
                load_freqs(fn_freqs);
            }

            void init(string fn_stations, string fn_probs, string fn_times,
                    string fn_paths)
            {
                load_probs(fn_probs);
                load_stations(fn_stations);
                load_times(fn_times);
                load_paths(fn_paths);
            }

            void init(string fn_stations, string fn_times, string fn_paths)
            {
                cout << "Loading stations..." << endl;
                load_stations(fn_stations);
                cout << "Loading times..." << endl;
                load_times(fn_times);
                cout << "Loading paths..." << endl;
                load_paths(fn_paths);
            }

            void reload(string fn_times, string fn_paths)
            {
                cout << "Loading times..." << endl;
                reload_times(fn_times);
                cout << "Loading paths..." << endl;
                reload_paths(fn_paths);
            }

            void load_probs(string fn_probs)
            {
                int tau, day, pickup, dropoff;
                double prob;
                ifstream data(fn_probs);
                string line;
                getline(data, line);

                double lp = 0;
                while(getline(data, line))
                {
                    stringstream lineStream(line);
                    string cell;
                    int counter = 0;
                    while(std::getline(lineStream, cell, ','))
                    {
                        switch (counter++)
                        {
                            case 0: tau = stoi(cell);
                            case 1: day = stoi(cell);
                            case 2: pickup = stoi(cell);
                            case 3: dropoff = stoi(cell);
                            case 4: prob = stof(cell);
                            default: break;
                        }
                    }

                    Demand dem(tau, day, pickup, dropoff);
                    demands[dem] = prob;
                    demand_vec.push_back(dem);
                    cum_sum.push_back(lp + prob);
                    lp += prob;
                }
            }

            void load_stations(string fn_stations)
            {
                double lat, lon;
                ifstream data(fn_stations);
                string line;
                getline(data, line);

                while(getline(data, line))
                {
                    stringstream lineStream(line);
                    string cell;
                    int counter = 0;
                    while(std::getline(lineStream, cell, ','))
                    {
                        switch (counter++)
                        {
                            case 1: lat = stof(cell);
                            case 2: lon = stof(cell);
                            default: break;
                        }
                    }
                    stations.push_back(GeoLocation(lat, lon));
                }
            }

            void reload_times(string fn_times)
            {
                times.clear();
                load_times(fn_times);
            }

            void load_times(string fn_times)
            {
                ifstream data(fn_times);
                string line;
                getline(data, line);

                while(getline(data, line))
                {
                    times.push_back(vector<double>());
                    stringstream lineStream(line);
                    string cell;
                    while(std::getline(lineStream, cell, ' '))
                    {
                        times.back().push_back(stof(cell));
                    }
                }
            }

            void reload_paths(string fn_paths)
            {
                paths.clear();
                load_paths(fn_paths);
            }

            void load_paths(string fn_paths)
            {
                ifstream data(fn_paths);
                string line;

                while(getline(data, line))
                {
                    stringstream lineStream(line);
                    string cell;
                    std::getline(lineStream, cell, ' ');
                    int start = stoi(cell);
                    std::getline(lineStream, cell, ' ');
                    int end = stoi(cell);
                    if (paths.count(start) == 0)
                    {
                        paths[start] = unordered_map<int, vector<int>>();
                    }
                    paths[start][end] = vector<int>();
                    while(std::getline(lineStream, cell, ' '))
                    {
                        paths[start][end].push_back(stoi(cell));
                    }
                }
            }

            void load_freqs(string fn_freqs)
            {
                int interval;
                float expected_reqs;
                ifstream data(fn_freqs);
                string line;
                getline(data, line);

                while(getline(data, line))
                {
                    stringstream lineStream(line);
                    string cell;
                    int counter = 0;
                    while(std::getline(lineStream, cell, ','))
                    {
                        switch (counter++)
                        {
                            case 0: interval = stoi(cell);
                            case 1: expected_reqs = (int) stof(cell);
                            default: break;
                        }
                    }
                    freqs[interval] = expected_reqs;
                }
            }

            bool get_path(int start, int end, vector<int>& path,
                    vector<double>& inter_times)
            {
                // returns true if there is a path, false if there isn't
                double time_edge = 0;
                if (paths.count(start) > 0 and paths[start].count(end) > 0)
                {
                    path = paths[start][end];
                    inter_times.push_back(time_edge);
                    for (size_t i = 0; i < path.size() - 1; i++)
                    {
                        time_edge = times[path[i]][path[i + 1]];
                        inter_times.push_back(time_edge);
                    }
                    return true;
                }
                else
                {
                    return false;
                }
            }

            double get_travel_time_estimate(double lat, double lon, int station)
            {
                GeoLocation gl(lat, lon);
                int closest_station = get_station(gl);
                double dist = get_station(closest_station).distance(gl);
                return dist + times[closest_station][station];
            }

            double get_travel_time(int station1, int station2) const
            {
                return times[station1][station2];
            }

            int get_station(GeoLocation gl)
            {
                double min_dist;
                int min_id;
                for (size_t i = 0; i < stations.size(); i++)
                {
                    double dist = stations[i].distance(gl);
                    if (i == 0)
                    {
                        min_id = 0;
                        min_dist = dist;
                    }
                    else
                    {
                        if (dist < min_dist)
                        {
                            min_id = i;
                            min_dist = dist;
                        }
                    }
                }
                return min_id;
            }

            GeoLocation get_station(int id)
            {
                return stations[id];
            }

            double query_demand(Demand dem)
            {
                if (demands.count(dem) > 0)
                {
                    return demands[dem];
                }
                else
                {
                    return 0;
                }
            }

            double query_demand(int tau, int day, int pickup, int dropoff)
            {
                return query_demand(Demand(tau, day, pickup, dropoff));
            }

            double query_demand(int secs, int day, GeoLocation pickup,
                    GeoLocation dropoff)
            {
                int p_st = get_station(pickup);
                int d_st = get_station(dropoff);
                int tau = secs / (60 * 15);
                return query_demand(tau, day, p_st, d_st);
            }

            void sample(int num, vector<double>& csum, int offset,
                    vector<Demand>& dems)
            {
                for (int i = 0; i < num; i++)
                {
                    double rnd = (double) rand() / (double) (RAND_MAX);
                    double r = csum[0] + (csum.back() - csum[0]) * rnd;
                    for (size_t j = 0; j < csum.size(); j++)
                    {
                        if (r < csum[j])
                        {
                            dems.push_back(demand_vec[j + offset]);
                            break;
                        }
                    }
                }
            }

            bool sample(int num, Time st, Time end, vector<Demand>& dems)
            {
                // This returns true if something was actually sampled
                // This only works if the probability file is sorted by time
                vector<double> csum;
                double lp = 0;
                int offset = -1;
                int expected_reqs = compute_number_of_samples(st, end);
                if (num > expected_reqs)
                {
                    num = expected_reqs;
                }
                for (size_t i = 0; i < demand_vec.size(); i++)
                {
                    if (end <= demand_vec[i])
                    {
                        break;
                    }

                    if (st <= demand_vec[i])
                    {
                        if (offset < 0)
                        {
                            offset = i;
                        }
                        csum.push_back(lp + demands[demand_vec[i]]);
                        lp += demands[demand_vec[i]];
                    }
                }
                if (csum.size() > 0)
                {
                    sample(num, csum, offset, dems);
                    return true;
                }
                else
                {
                    return false;
                }
            }

            int compute_number_of_samples(Time st, Time end)
            {
                int s_int = st.get_interval();
                int e_int = end.get_interval();
                int expected_reqs = 0;
                for (int i = s_int; i <= e_int; i++)
                {
                    expected_reqs += freqs[i];
                }
                return expected_reqs;
            }
    };
};

#endif
