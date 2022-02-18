//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include "common.h"
#include "strategy.h"
#include <time.h>
#include <string.h>
#include <any>
#include <map>
#include "contract.h"
                   //
//using namespace std;
//
#if 0
struct TimeSeries {
public:
    void add(double v, const time_t &t) {
        m_v = v; m_tm = t;
        m_vars->push_back(v);
        m_tms->push_back(t);
    }

public:
    double m_v {0};
    time_t m_tm {0};
private:
    std::vector<double> *m_vars {nullptr};
    std::vector<time_t> *m_tms{nullptr};
};
#endif

struct LiveData {
    double bid,ask,last;
    double bSize,aSize,lSize;
    double oday, cprev;
    double hday, lday;
    double vdayp;
    LiveData () {
        memset(this, 0, sizeof(*this));
    }
    operator const std::string () const {
        #define OUT_F(t) os << #t << ": " << t << ","
        std::ostringstream os;
        os << "oday:" << oday << "," << "cprev:" << cprev << ",";
        os << "hday:" << hday << "," << "lday:" << lday << ",";
        os << "vdayp:" << vdayp << ",";

        OUT_F(oday); OUT_F(cprev);
        OUT_F(hday); OUT_F(lday);
        OUT_F(vdayp);
        OUT_F(bid);
        OUT_F(bSize);
        OUT_F(ask);
        OUT_F(aSize);
        OUT_F(last);
        OUT_F(lSize);
        #undef OUT_F

        return os.str();
    }

};
struct SnapData {
    const int Y20 = 24 *3600 * 365 * 20;
    SnapData(const std::string &symbol, int idx, BigTable *p) : symbol(symbol),idx(idx),pTable(p) {

    }
    bool  isAvailable() { return  idx != -1;} 
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
        // log->debug("idx:{},sym:{},open:{},close:{},high:{},low:{},volume:{},tm:{}", idx, symbol, open, close, high, low,volume,buf); 
        log->debug("idx:{},sym:{}:liveData:{}", idx, symbol,(const string)liveData);
    }
    void update(float o, float h, float l, float c, int v, time_t t) {
        open = o;
        close = c;
        high = h;
        low = l;
        volume = v;
        tm = t;
    }
    int idx ;
    BigTable * pTable {nullptr};
    std::unique_ptr<ContractDetails> ibContractDetails {nullptr};
    bool ibUpdated {false};
    LiveData liveData;
    std::string symbol;
    float open {0.0};
    float close {0.0};
    float high {0.0};
    float low {0.0};
    int   volume {0};
    time_t tm {0};
};
using SnapDataMap= std::map<std::string, SnapData>;
