cmake_minimum_required(VERSION 3.10)


set(CC_DIR /usr/local/Cellar/gcc/11.2.0_3)
set(CC ${CC_DIR}/bin/gcc)
set(CXX "${CC_DIR}/bin/g++-11")
set(AR "${CC_DIR}/bin/gcc-ar-11")

#set(CMAKE_CXX_FLAGS "-g")
#set(CMAKE_CXX_FLAGS "-g -pthread -Wall -Wno-switch -Wpedantic -Wno-unused-function")

# set the project name
#set(CMAKE_C_FLAGS "-pthread -Wall -Wno-switch -Wpedantic -Wno-unused-function")
#set(CMAKE_CXX_FLAGS "-pthread -Wall -Wno-switch -Wpedantic -Wno-unused-function")
#include_directories(client)
project(v_trade)
add_subdirectory(twsapi_1014.01)

include_directories(/usr/local/Cellar/gcc/11.2.0_3/include)
link_directories(/usr/local/Cellar/gcc/11.2.0_3/lib)


#find_library(BID bid twsapi_1014.01/lib)

# add the executable
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

add_executable(main_lv IBTWSApp.cpp main_lv.cpp Scenario_v1.cpp ContractPairTrade.cpp Backtest.cpp)
target_link_libraries(main_lv gsl gslcblas  ${BID} tws_ib spdlog)
target_include_directories(main_lv PUBLIC twsapi_1014.01)

#add_executable(IBTWSApp IBTWSApp.cpp)
#target_link_libraries(IBTWSApp  tws_ib ${BID})
#target_include_directories(IBTWSApp   PUBLIC twsapi_1014.01)
