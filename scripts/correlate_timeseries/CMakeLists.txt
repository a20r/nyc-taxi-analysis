cmake_minimum_required (VERSION 2.6)
project (correlate_timeseries CXX)
add_definitions(-std=c++11 -Wall -Wextra)
find_package(
    Boost REQUIRED
    COMPONENTS date_time)
# find_package(GSL REQUIRED)

include_directories(${Boost_INCLUDE_DIRS})
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp")
add_executable(correlate_timeseries correlate_timeseries.cpp)
target_link_libraries(correlate_timeseries ${Boost_LIBRARIES})
