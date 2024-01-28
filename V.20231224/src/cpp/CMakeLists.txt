cmake_minimum_required(VERSION 3.10)

# Set the project name and version
project(v-trade VERSION 1.0)

# Specify the C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Set the build type to Debug for no optimizations and including debug symbols
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Debug)
endif()

# Set the source directories
set(TWS_CLIENT_SRC_DIR ${CMAKE_SOURCE_DIR}/twsapi_macunix.1019.02/IBJts/source/cppclient)

# Add the third-party libraries
add_subdirectory(csv-parser)
add_subdirectory(json)
add_subdirectory(spdlog)
add_subdirectory(clickhouse-cpp)

# Add the TwsSocketClient library
file(GLOB TWS_CLIENT_SRCS "${TWS_CLIENT_SRC_DIR}/client/*.cpp")
add_library(TwsSocketClient SHARED ${TWS_CLIENT_SRCS})
target_include_directories(TwsSocketClient PUBLIC ${TWS_CLIENT_SRC_DIR} ${TWS_CLIENT_SRC_DIR}/client)

# Add the executable
add_executable(v-trade
    CmdOption.cpp
    Ohlcv.cpp
    V_IB_Sender.cpp  V_IB_Receiver.cpp
    v-main.cpp
    v_scanner.cpp v_news.cpp
    v_tws_events.cpp v_tws_history.cpp
    twsapi_macunix.1019.02/IBJts/samples/Cpp/TestCppClient/Utils.cpp
)

# Link the executable with required libraries
target_link_libraries(v-trade
    TwsSocketClient
    csv
    nlohmann_json::nlohmann_json
    spdlog::spdlog
    ${CMAKE_SOURCE_DIR}/IntelRDFPMathLib20U2/LIBRARY/libbid.a # Direct path to the static library
    clickhouse-cpp-lib
)

# Set include directories for the executable
target_include_directories(v-trade PRIVATE
    csv-parser/include
    clickhouse-cpp/ clickhouse-cpp/contrib/absl
    ${CMAKE_SOURCE_DIR}/twsapi_macunix.1019.02/IBJts/samples/Cpp/TestCppClient
)


# Generate compile_commands.json for Clangd support
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

