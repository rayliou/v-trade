#include "Ohlcv.h"
#include "utility.h" // Assuming utility functions like decimalToDouble are defined here.

Ohlcv::Ohlcv() {}

Ohlcv::Ohlcv(std::string symbol) : symbol(symbol) {}

bool Ohlcv::isNan() const { return open < 0; }

Ohlcv &Ohlcv::operator=(const Ohlcv &o) {
    // Copy assignment from another Ohlcv object.
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

Ohlcv &Ohlcv::operator=(const Bar &b) {
    // Copy assignment from a Bar object.
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

void Ohlcv::dump(std::ostream &os, bool withValue, bool withName,
                 bool withTime) const {
// Implementation of dump function.
#define OUT_F(t)                                                               \
    {                                                                          \
        if (withName)                                                          \
            os << #t << '_' << symbol;                                         \
        if (withName && withValue)                                             \
            os << ":";                                                         \
        if (withValue)                                                         \
            os << t;                                                           \
        os << ',';                                                             \
    }
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

Ohlcv::operator const std::string() const {
    // Conversion to std::string.
    std::ostringstream os;
    dump(os, true, true);
    return os.str();
}

void Ohlcv::debug(LogType log) {
    // Debug function implementation.
    log->debug("{}", static_cast<const std::string>(*this));
}
