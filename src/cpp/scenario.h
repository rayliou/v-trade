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
#include <any>
                   //
//using namespace std;
//
struct SnapData {
    const int Y20 = 24 *3600 * 365 * 20;
    SnapData(const std::string &symbol) : symbol(symbol) {

    }
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
    IScenario(CmdOption &cmd) :m_cmdOption(cmd) {
        auto var = m_cmdOption.get("--includes");
        if (nullptr != var) {
            auto symbols = strSplit(var,',');
            std::for_each(symbols.begin(), symbols.end(), [&] (auto &s) {  m_includes.insert(s);} );
        }
        var  = m_cmdOption.get("--excludes");
        if (nullptr != var) {
            auto symbols = strSplit(var,',');
            std::for_each(symbols.begin(), symbols.end(), [&] (auto &s) {  m_excludes.insert(s);} );
        }

    }
    virtual std::vector<SnapData> &  getSnapDataList()  = 0;
    virtual void postSetup() = 0;
    virtual void runOneEpoch(const std::pair<std::string, time_t>  & cur,const std::pair<std::string, time_t>  & start ) = 0;
    virtual void preOneEpoch(const std::map<std::string, std::any>& ext) = 0;
    virtual void postOneEpoch(const std::map<std::string, std::any>& ext) = 0;
    virtual std::string getConfPath() const= 0;
    // virtual void summary(const std::map<std::string, std::any>& ext) = 0;
    virtual void debug(LogType *log) = 0;
    virtual ~IScenario() {}
protected:
    CmdOption & m_cmdOption;
    std::set<std::string> m_excludes;
    std::set<std::string> m_includes;
};
