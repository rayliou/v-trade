//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include "common.h"
#include <iostream>

#include "bar.h"

struct Ohlcv {
    Ohlcv () {}
    Ohlcv (std::string symbol):symbol(symbol){}
    float open {-1.};
    float close {-1.};
    float high {-1.};
    float low {-1.};
    int   volume {-1};
    double wap {-1.};
    time_t tm {0};
    std::string tmStr ;
    std::string vStr ;
    std::string symbol;
    bool isNan() const {return open < 0;}
    Ohlcv  & operator = (const Ohlcv & o) {
        open = o.open;
        high = o.high;
        low = o.low;
        close = o.close;
        volume = o.volume;
        wap = o.wap;
        tmStr = o.tmStr;
        vStr = o.vStr;
        symbol = o.symbol;
        return *this;
    }
    Ohlcv  & operator = (const Bar & b) {
        open = b.open;
        high = b.high;
        low = b.low;
        close = b.close;
        volume = decimalToDouble(b.volume);
        wap = decimalToDouble(b.wap);
        tmStr = b.time;
        vStr = decimalToString(b.volume);
        return *this;
    }
    void dump(std::ostream &os, bool withValue = true, bool withName = false){
        #define OUT_F(t)  { if(withName) os << #t << '_' << symbol ; if(withName && withValue) os << ":"; if(withValue) os << t; os << ','; }
        OUT_F(open);
        OUT_F(high);
        OUT_F(low);
        OUT_F(close);
        OUT_F(volume);
        OUT_F(wap);
        #undef OUT_F

    }
    operator const std::string () const {
        #define OUT_F(t) os << #t << ": " << t << ","
        std::ostringstream os;
        OUT_F(tmStr); OUT_F(symbol);
        OUT_F(open); OUT_F(high);
        OUT_F(low); OUT_F(close);
        OUT_F(volume); OUT_F(wap);
        OUT_F(vStr);
        #undef OUT_F

        return os.str();
    }

    void debug(LogType log) { 
        log->debug("{}",(const string)(*this));
    }
using ValuesOhlcv = std::vector<Ohlcv>;
using RowOhlcv = std::pair<string, ValuesOhlcv>;
using TimeMapOhlcv = std::map<string, std::vector<Ohlcv>>;
static void dump(TimeMapOhlcv &m, std::ostream &os) {
    if(m.size() == 0) {
        return;
    }
    auto &[t,v] = *m.begin();
    os << "time" << ',';
    for(auto & ohlcv: v){
        ohlcv.dump(os,false,true);
    }
    os << std::endl;
    for(auto &[t,v]:m) {
        os << t << ',';
        for(auto & ohlcv: v){
            ohlcv.dump(os,true);
        }
        os << std::endl;

    }
    return;
}


};
