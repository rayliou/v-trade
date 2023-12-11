#pragma once
#include "common.h"
#include "bar.h"
#include <ctime>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <vector>

// Structure representing Open-High-Low-Close-Volume (OHLCV) data.
struct Ohlcv {
    // Default constructor.
    Ohlcv();

    // Constructor with symbol initialization.
    Ohlcv(std::string symbol);

    // Member variables representing OHLCV data.
    float open{-1.};
    float close{-1.};
    float high{-1.};
    float low{-1.};
    int volume{-1};
    double wap{-1.};
    time_t tm{0};
    std::string tmStr;
    std::string vStr;
    std::string symbol;

    // Checks if the OHLCV data is not initialized.
    bool isNan() const;

    // Assignment operator overloads for OHLCV and Bar structures.
    Ohlcv &operator=(const Ohlcv &o);
    Ohlcv &operator=(const Bar &b);

    // Dumps the OHLCV data to an output stream.
    void dump(std::ostream &os, bool withValue = true, bool withName = false,
              bool withTime = false) const;

    // Conversion operator to std::string.
    operator const std::string() const;

    // Debug function to log OHLCV data.
    void debug(LogType log);

    // Type aliases for OHLCV data collections.
    using ValuesOhlcv = std::vector<Ohlcv>;
    using RowOhlcv = std::pair<std::string, ValuesOhlcv>;
    using TimeMapOhlcv = std::map<std::string, std::vector<Ohlcv>>;
};
