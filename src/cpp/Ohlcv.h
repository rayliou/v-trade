//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include "common.h"
#include <iostream>
#include <set>

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
        tm = o.tm;
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
        tm = utility::to_time_t(tmStr.c_str());
        vStr = decimalToString(b.volume);
        return *this;
    }
    void dump(std::ostream &os, bool withValue = true, bool withName = false, bool withTime=false) const{
        #define OUT_F(t)  { if(withName) os << #t << '_' << symbol ; if(withName && withValue) os << ":"; if(withValue) os << t; os << ','; }
        OUT_F(open);
        OUT_F(high);
        OUT_F(low);
        OUT_F(close);
        OUT_F(volume);
        OUT_F(wap);
        if (withTime) {
            OUT_F(tm);
        }
        #undef OUT_F

    }
    operator const std::string () const {
        std::ostringstream os;
        dump(os,true,true);
        return os.str();
    }

    void debug(LogType log) { 
        log->debug("{}",(const string)(*this));
    }
using ValuesOhlcv = std::vector<Ohlcv>;
using RowOhlcv = std::pair<string, ValuesOhlcv>;
using TimeMapOhlcv = std::map<string, std::vector<Ohlcv>>;

};
