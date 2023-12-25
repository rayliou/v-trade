#pragma once

#include <map>
#include <vector>
#include <string>
#include <vector>
#include <list>
#include <sstream>

#include "utility.h"

// #include "./3rd-party/JohansenCointegration/JohansenHelper.h"

//https://github.com/gabime/spdlog

#include "spdlog/spdlog.h"
#include "spdlog/sinks/stdout_color_sinks.h"
#include "spdlog/cfg/env.h"

// https://github.com/nlohmann/json
// https://github.com/nlohmann/json/blob/develop/doc/examples/README.cpp
#include "nlohmann/json.hpp"
using json = nlohmann::json;

//https://github.com/vincentlaucsb/csv-parser
#include "csv.hpp"
using LogType = std::shared_ptr<spdlog::logger>;

// #include "BigTable.h"
// #include "icontract.h"

#include "VContract.h"
