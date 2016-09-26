cmake_minimum_required (VERSION 2.6)
project (create_timeseries CXX)
add_definitions(-std=c++11 -Wall -Wextra)
find_package(
    Boost REQUIRED
    COMPONENTS date_time)
include_directories(${Boost_INCLUDE_DIRS})
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp")
add_executable(create_timeseries create_timeseries.cpp)
target_link_libraries(create_timeseries ${Boost_LIBRARIES})
