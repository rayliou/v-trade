//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once

#include <map>
#include <string>
#include <vector>
#include <list>
#include <sstream>

#include "3rd-party/spdlog/include/spdlog/spdlog.h"
#include "3rd-party/spdlog/include/spdlog/sinks/stdout_color_sinks.h"
#include "3rd-party/csv-parser/single_include/csv.hpp"
// https://github.com/nlohmann/json
//#include "3rd-party/json/single_include/nlohmann/json.hpp"

//https://github.com/vincentlaucsb/csv-parser
#include "3rd-party/csv-parser/single_include/csv.hpp"

using LogType = std::shared_ptr<spdlog::logger>;


inline std::list<std::string>  strSplit(std::string str, char delim) {
    std::list<std::string> ret;
    std::istringstream ss(str);
    std::string v;
    while( getline(ss, v, delim)){
        ret.push_back(v);
    }
    return ret;
}

class CmdOption {
public:
    CmdOption(int argc, char * argv[]) :m_argc(argc),m_argv(argv) {
    }

    char* get(const std::string & option)
    {
        auto begin = m_argv;
        auto end = m_argv + m_argc;
        char ** itr = std::find(begin,end, option);
        if (itr != end && ++itr != end)
        {
            return *itr;
        }
        return nullptr;
    }
    std::list<std::string> getM(const std::string & option)
    {
         std::list<std::string> ret;
        auto begin = m_argv;
        auto end = m_argv + m_argc;
        char ** itr = std::find(begin,end, option);
        if (nullptr == itr) {
            return ret;
        }
        for(itr++;(itr != end && **itr != '-' ) ; itr++) {
            ret.push_back(*itr);
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
    int m_argc;
    char ** m_argv;
};
