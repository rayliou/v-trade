//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once

#include <map>
#include <vector>

#include "3rd-party/spdlog/include/spdlog/spdlog.h"
#include "3rd-party/spdlog/include/spdlog/sinks/stdout_color_sinks.h"
#include "3rd-party/csv-parser/single_include/csv.hpp"

using LogType = std::shared_ptr<spdlog::logger>;

