#include "BigTable.h"
#include <csv.h>     // Assuming csv.h is available and has relevant functions.
#include <utility.h> // Assuming utility.h is available and has relevant functions.

int BigTable::getSymbolIndex(const std::string &symbol) const {
    // Implementation of getSymbolIndex.
    auto it = m_symbolToColIdx.find(symbol);
    if (m_symbolToColIdx.end() == it) {
        return -1;
    }
    return it->second;
}

void BigTable::debug(LogType log) {
    // Implementation of debug.
    ostringstream os;
    for (auto &f : m_sourceList) {
        os << f << ",";
    }
    log->debug("BigTable: srcList: {}", os.str());
}

void BigTable::load(std::string fileName) {
    // Implementation of load.
    using namespace csv;
    using namespace std;
    using namespace utility;
    /*****************
     * time	open_AAPL	high_AAPL	low_AAPL	close_AAPL	volume_AAPL	wap_AAPL
     * open_ACN	high_ACN	low_ACN 20220126  12:00:00	162.85 162.9
     * 162.84	162.9	107	162.883	340.07	340.07	340.07
     * ************/
    m_sourceList.push_back(fileName);

    CSVReader reader(fileName);
    Ohlcv::ValuesOhlcv valuesOhlcv;
    set<string> symbols;
    for (auto col : reader.get_col_names()) {
        col = trim(col);
        if (col.empty()) {
            continue;
        }
        auto v = strSplit(col, '_');
        if (v.size() == 2) {
            auto s = v[1];
            symbols.insert(s);
        }
    }
    int cnt = 0;
    for (auto &s : symbols) {
        valuesOhlcv.push_back(Ohlcv(s));
        m_symbolToColIdx[s] = cnt++;
    }
    for (auto &row : reader) {
        string strTime = row["time"].get<>();
        Ohlcv::ValuesOhlcv values(valuesOhlcv);
        for (auto &v : values) {
#define FILL(x) v.x = row[#x "_" + v.symbol].get<double>()
            FILL(open);
            FILL(high);
            FILL(low);
            FILL(close);
            FILL(volume);
            FILL(wap);
            v.tmStr = strTime;
            v.tm = utility::to_time_t(v.tmStr.c_str());
#undef FILL
        }
        insert({strTime, values});
    }
}

void BigTable::dump(std::ostream &os) {
    // Implementation of dump.
    if (size() == 0) {
        return;
    }
    auto &[t, v] = *begin();
    os << "time" << ',';
    for (auto &ohlcv : v) {
        ohlcv.dump(os, false, true);
    }
    os << std::endl;
    for (auto &[t, v] : *this) {
        os << t << ',';
        for (auto &ohlcv : v) {
            ohlcv.dump(os, true);
        }
        os << std::endl;
    }
    return;
}

std::ostream &operator<<(std::ostream &o, BigTable &b) {
    // Implementation of stream insertion operator.
    b.dump(o);
    return o;
}
