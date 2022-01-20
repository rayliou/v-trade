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
#include <time.h>
                   //
//using namespace std;
//
struct SnapData {
    const int Y20 = 24 *3600 * 365 * 20;
    SnapData(const std::string &symbol) : symbol(symbol) {}
    void debug(LogType log) { 
#if 0
        if (tm == 0) {
            tm = time(&tm);
        }
        else {
            time_t n;
            time(&n);
            if ( abs(tm -n) > Y20 ){
                log->error("tm error {}", tm);
                throw std::runtime_error("Time error");
            }
        }
#endif

        char buf[64];
        ctime_r(&tm, buf);
        //std::ctime_s(&buf, sizeof(buf),&tm);
        log->debug("idx:{},sym:{},open:{},close:{},high:{},low:{},volume:{},tm:{}", idx, symbol, open, close, high, low,volume,buf); 
    }
    void update(float o, float h, float l, float c, int v, time_t t) {
        open = o;
        close = c;
        high = h;
        low = l;
        volume = v;
        tm = t;
    }
    int idx {-1};
    std::string symbol;
    float open {0.0};
    float close {0.0};
    float high {0.0};
    float low {0.0};
    int   volume {0};
    time_t tm {0};
};


class IScenario {
public:
    virtual std::vector<SnapData> &  getSymbolList()  = 0;
    virtual void postSetup() = 0;
    virtual void execute() = 0;
    virtual void debug(LogType *log) = 0;
    virtual ~IScenario() {}
};
