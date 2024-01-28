// /usr/local/Cellar/gcc/11.2.0_3/bin/g++-11 -g  -std=gnu++20 -I/usr/local/Cellar/gcc/11.2.0_3/include  -I3rd-party/spdlog/include    common.h
#ifndef __common_h__
#define  __common_h__

//#pragma once

#include <map>
#include <string>
#include <vector>
#include <list>
#include <sstream>

#include "utility.h"

#include "./3rd-party/JohansenCointegration/JohansenHelper.h"

//https://github.com/gabime/spdlog
// https://github.com/nlohmann/json
// https://github.com/nlohmann/json/blob/develop/doc/examples/README.cpp
#if 0
#include "3rd-party/spdlog/include/spdlog/spdlog.h"
#include "3rd-party/spdlog/include/spdlog/sinks/stdout_color_sinks.h"
#include "3rd-party/spdlog/include/spdlog/cfg/env.h"

#include "3rd-party/json/single_include/nlohmann/json.hpp"
#else
#include "spdlog/spdlog.h"
#include "spdlog/sinks/stdout_color_sinks.h"
#include "spdlog/cfg/env.h"
#include "nlohmann/json.hpp"
#endif
using json = nlohmann::json;

//https://github.com/vincentlaucsb/csv-parser
#include "3rd-party/csv-parser/single_include/csv.hpp"
using LogType = std::shared_ptr<spdlog::logger>;

#include "BigTable.h"
#include "icontract.h"

////////////////////////// String ulti

class CmdOption {
public:
    CmdOption(int argc, char * argv[]) :m_argc(argc),m_argv(argv) {
    }

    char* get(const std::string & option) {
        auto begin = m_argv;
        auto end = m_argv + m_argc;
        return _get(option, begin, end);

    }
    std::vector<std::string> getM(const std::string & option)
    {
        std::vector<std::string> ret;
        auto begin = m_argv;
        auto end = m_argv + m_argc;
        char ** last = begin;
        char * s ;
        while ( nullptr != ( s = _get(option, last, end, &last) )) {
            ret.push_back(s);
        }
        return ret;
    }
    bool exists(const std::string & option) {
        auto begin = m_argv;
        auto end = m_argv + m_argc;
        char ** itr = std::find(begin, end, option);
        return itr != end;
    }
    std::string str() const  {
        std::ostringstream ss;
        for (auto it = m_argv; it != m_argv + m_argc; it++) {
            ss << (*it);
            ss << " ";
        }
        return ss.str();
    }
private:
    char* _get(const std::string & option, char ** begin, char ** end, char ***last = nullptr) {
        char ** itr = std::find(begin,end, option);
        if (itr != end && ++itr != end)
        {
            if ( nullptr != last) {
                *last = itr +1;
            }
            return *itr;
        }
        return nullptr;
    }
private:
    int m_argc;
    char ** m_argv;
};
#endif  //__common_h__
