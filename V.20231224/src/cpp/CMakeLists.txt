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


# Add include directories
#include_directories(${PROJECT_SOURCE_DIR})

# If spdlog is not installed system-wide, specify its path here
# include_directories(${PROJECT_SOURCE_DIR}/spdlog)

include_directories(csv-parser/include)
add_subdirectory(csv-parser)
# https://github.com/nlohmann/json
add_subdirectory(json)
add_subdirectory(spdlog)

set(TWS_CLIENT_SRC_DIR ${CMAKE_SOURCE_DIR}/twsapi_macunix.1019.02/IBJts/source/cppclient)

include_directories(${TWS_CLIENT_SRC_DIR})
include_directories(${TWS_CLIENT_SRC_DIR}/client)
file(GLOB TWS_CLIENT_SRCS "${TWS_CLIENT_SRC_DIR}/client/*.cpp")
add_library(TwsSocketClient SHARED ${TWS_CLIENT_SRCS})
# Set compile options
#target_compile_options(TwsSocketClient PRIVATE 
    #-pthread 
    #-Wall 
    #-Wno-switch 
    #-Wno-unused-function
#)

# Set the property to compile with Position Independent Code
#set_target_properties(TwsSocketClient PROPERTIES POSITION_INDEPENDENT_CODE ON)
#target_include_directories(TwsSocketClient PUBLIC ${TWS_CLIENT_SRC_DIR})
# Set custom compiler and linker
#set_target_properties(TwsSocketClient PROPERTIES
    #CXX_COMPILER_LAUNCHER g++-12
    ## LINKER_LANGUAGE CXX
    #CXX_STANDARD 17
#)

# Linker Flags
#set_target_properties(TwsSocketClient PROPERTIES LINK_FLAGS "-pthread")

include_directories(${CMAKE_SOURCE_DIR}/twsapi_macunix.1019.02/IBJts/samples/Cpp//TestCppClient)

#- https://www.intel.com/content/www/us/en/developer/articles/tool/intel-decimal-floating-point-math-library.html
#- https://www.netlib.org/misc/intel/
# libbid.a
link_directories(${CMAKE_SOURCE_DIR}/IntelRDFPMathLib20U2/LIBRARY)

# Add source files
add_executable(v-trade
    CmdOption.cpp
    Ohlcv.cpp
    V_IB_EClientSocket.cpp  V_IB_EWrapper.cpp
    v-main.cpp
    twsapi_macunix.1019.02/IBJts/samples/Cpp//TestCppClient/Utils.cpp
)

# Link libraries (if necessary)
# For example, if you have additional libraries to link against:
target_link_libraries(v-trade
    TwsSocketClient
    csv
    nlohmann_json::nlohmann_json
    spdlog::spdlog
    bid
    )

# Generate compile_commands.json for Clangd support
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

