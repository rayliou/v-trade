//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#if 0
#include <string>
#include <fstream>
#include <vector>
#include <utility> // std::pair
#include <stdexcept> // std::runtime_error
#include <sstream> // std::stringstream
#include <iostream>
#include <tuple>
#include <map>
#include <time.h>
#endif
#include "contract.h"
#include "strategy.h"
                   //
//using namespace std;
//
struct SnapData {
    SnapData(const std::string &symbol) : symbol(symbol) {}
    void debug(LogType log) { log->debug("idx:{},sym:{},open:{},close:{},high:{},low:{},volume:{}",idx, symbol, open, close, high, low,volume); }
    int idx {-1};
    std::string symbol;
    float open {0.0};
    float close {0.0};
    float high {0.0};
    float low {0.0};
    int   volume {0};
};


class IScenario {
public:
    virtual std::vector<SnapData> &  getSymbolList()  = 0;
    virtual void execute() = 0;
    virtual ~IScenario() {}
};
