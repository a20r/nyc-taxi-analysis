
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
#include "cnpy.h"

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

    class MultiArray
    {
        public:
            cnpy::NpyArray arr;

            MultiArray() {}

            MultiArray(cnpy::NpyArray arr) : arr(arr)
            {
                data = reinterpret_cast<int*>(arr.data);
            }

            ~MultiArray()
            {
                arr.destruct();
                delete[] data;
            }

            int compute_index(int interval, int day, int pickup, int dropoff)
            {
                int D1 = arr.shape[1], D2 = arr.shape[2], D3 = arr.shape[3];
                int index = interval * D1 * D2 * D3
                    + day * D2 * D3 + pickup * D3 + dropoff;
                return index;
            }

            Demand compute_coords(int index)
            {
                int D1 = arr.shape[0], D2 = arr.shape[1], D3 = arr.shape[2];
                int D4 = arr.shape[3];
                int inter = index % D1;
                int day = ((index - inter) / D1) %  D2;
                int pick = ((index - day * D1 - inter) / (D1 * D2)) % D3;
                int drop = ((index - pick * D2 * D1 - day * D1 - inter)
                        / (D1 * D2 * D3) ) % D4;
                return Demand(inter, day, pick, drop);
            }

            int get(int index)
            {
                return data[index];
            }

            int get(int interval, int day, int pickup, int dropoff)
            {
                return get(compute_index(interval, day, pickup, dropoff));
            }

        private:
            int *data;
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
            vector<int> station_ids;
            unordered_map<int, GeoLocation> stations_map;
            vector<vector<double>> times;
            unordered_map<int, unordered_map<int, vector<int>>> paths;
            unordered_map<int, int> freqs;
            MultiArray *freqs_ma;

        public:
            DemandLookup() {};

            ~DemandLookup()
            {}

            DemandLookup(string fn_stations, string fn_freqs, string fn_times,
                    string fn_paths)
            {
                init(fn_stations, fn_freqs, fn_times, fn_paths);
            }

            void init(string fn_stations, string fn_freqs, string fn_times,
                    string fn_paths)
            {
                cout << "Loading freqs..." << endl;
                load_freqs(fn_freqs);
                cout << "Loading stations..." << endl;
                load_stations(fn_stations);
                cout << "Loading times..." << endl;
                load_times(fn_times);
                cout << "Loading paths..." << endl;
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

            void load_freqs(string fn_freqs)
            {
                cnpy::NpyArray arr = cnpy::npy_load(fn_freqs);
                freqs_ma = new MultiArray(arr);
            }

            void load_stations(string fn_stations)
            {
                double lat, lon;
                int id;
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
                            case 0: id = stoi(cell);
                            case 1: lat = stof(cell);
                            case 2: lon = stof(cell);
                            default: break;
                        }
                    }
                    GeoLocation st(lat, lon);
                    stations.push_back(st);
                    stations_map[id] = st;
                    station_ids.push_back(id);
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

            double get_travel_time_estimate(double lat, double lon,
                    int station)
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
                            min_id = station_ids[i];
                            min_dist = dist;
                        }
                    }
                }
                return min_id;
            }

            GeoLocation get_station(int id)
            {
                return stations_map[id];
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

            bool sample(int num, Time st, Time end, vector<Demand>& dems)
            {
                int st_int = st.get_interval();
                int end_int = end.get_interval();
                int n_stations = freqs_ma->arr.shape[2];
                vector<double> csum;
                vector<Demand> ref_demands;
                int freq_sum = 0;

                for (int inter = st_int; inter <= end_int; inter++)
                {
                    for (int day = st.day; day <= end.day; day++)
                    {
                        for (int pick = 0; pick < n_stations; pick++)
                        {
                            for (int drop = 0; drop < n_stations; drop++)
                            {
                                int freq = freqs_ma->get(
                                        inter, day, pick, drop);
                                int pick_node = station_ids[pick];
                                int drop_node = station_ids[drop];
                                ref_demands.push_back(
                                        Demand(inter, day, pick_node,
                                            drop_node));
                                csum.push_back(freq_sum + freq);
                                freq_sum += freq;
                            }
                        }
                    }
                }

                if (csum.size() > 0)
                {
                    if (num > freq_sum / 52) {
                        num = freq_sum / 52;
                    }

                    for (int i = 0; i < num; i++)
                    {
                        double rnd = (double) rand() / (double) (RAND_MAX);
                        double r = csum[0] + (csum.back() - csum[0]) * rnd;
                        for (size_t j = 0; j < csum.size(); j++)
                        {
                            if (r < csum[j])
                            {
                                dems.push_back(ref_demands[j]);
                                break;
                            }
                        }
                    }
                    return true;
                }
                else
                {
                    return false;
                }
            }
    };
};

#endif
