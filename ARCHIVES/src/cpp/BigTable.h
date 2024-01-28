#pragma once
#include "Ohlcv.h"

class BigTable : public Ohlcv::TimeMapOhlcv {
public:
    //using iterator= Ohlcv::TimeMapOhlcv::iterator;
    //using const_iterator= Ohlcv::TimeMapOhlcv::const_iterator;

    int getSymbolIndex(const std::string &symbol) const {
        auto it = m_symbolToColIdx.find(symbol);
        if (m_symbolToColIdx.end() == it){
            return -1;
        }
        return it->second;
    }
    void debug(LogType log) {
        ostringstream os;
        for(auto &f: m_sourceList){
            os << f << ",";
        }
        log->debug("BigTable: srcList: {}", os.str());
    }
    void load(std::string fileName) {
        using namespace csv;
        using namespace std;
        using namespace utility;
        /*****************
         * time	open_AAPL	high_AAPL	low_AAPL	close_AAPL	volume_AAPL	wap_AAPL	open_ACN	high_ACN	low_ACN
         * 20220126  12:00:00	162.85	162.9	162.84	162.9	107	162.883	340.07	340.07	340.07
         * ************/
        m_sourceList.push_back(fileName);

        CSVReader reader(fileName);
        Ohlcv::ValuesOhlcv valuesOhlcv;
        set<string> symbols;
        for (auto col: reader.get_col_names()){
            col = trim(col);
            if(col.empty()) {
                continue;
            }
            auto v = strSplit(col,'_');
            if(v.size() == 2) {
                auto s = v[1];
                symbols.insert(s);
            }
        }
        int cnt =0;
        for(auto &s: symbols){
            valuesOhlcv.push_back(Ohlcv(s));
            m_symbolToColIdx[s] = cnt++;
        }
        for(auto &row:reader) {
            string strTime = row["time"].get<>();
            Ohlcv::ValuesOhlcv values(valuesOhlcv);
            for(auto &v: values) {
    #define FILL(x) v.x = row[ #x"_" + v.symbol].get<double>()
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
            insert( {strTime ,values});
        }
    }
    friend std::ostream & operator << (std::ostream &o, BigTable & b);
private:
void dump(std::ostream &os) {
        if(size() == 0) {
            return;
        }
        auto &[t,v] = *begin();
        os << "time" << ',';
        for(auto & ohlcv: v){
            ohlcv.dump(os,false,true);
        }
        os << std::endl;
        for(auto &[t,v]:*this) {
            os << t << ',';
            for(auto & ohlcv: v){
                ohlcv.dump(os,true);
            }
            os << std::endl;
        }
        return;
    }
private:
    std::list<std::string> m_sourceList;
    using SymbolToColIdx = map<string,int>;
    SymbolToColIdx m_symbolToColIdx;

} ;
inline std::ostream & operator << (std::ostream &o, BigTable & b) { b.dump(o); return o; }

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
#include "common.h"
                   //
using namespace std;

using IndexData =  vector<pair<string,time_t>>;
using ColumnData = vector<pair<std::string, std::vector<double>>>;
using SymbolToColIdx = map<string,int>;
using TableData = tuple<SymbolToColIdx,IndexData,ColumnData>;


class BigTable{
public:
    int m_fieldsNum {5};
    IndexData m_index;
    ColumnData m_columnData;
    SymbolToColIdx m_symbolToColIdx;
    std::string m_csvPath;

    BigTable(const char *csvPath):m_csvPath(csvPath) {
        this->read_csv(csvPath);
    }
    void debug(LogType &log) {
        std::ostringstream out;
        out << "Bigtable Path:\t" << m_csvPath << std::endl;
        out << "\tm_index:\t" << m_index.begin()->first << " to " << m_index.rbegin()->first  << std::endl;
        out << "\tsymbolToColIdx:\t" ;
        for(auto &[k,v]: m_symbolToColIdx) {
            out << k << ":" << v << ",";
        }
        log->debug("{}", out.str());
    }


    BigTable( const IndexData &index, const ColumnData &columnData, const SymbolToColIdx &symbolToColIdx)
    :m_index(index), m_columnData(columnData),m_symbolToColIdx(symbolToColIdx) { }

    vector<string>  getSymbolList() const  {

        vector<string> keys;
        std::transform(
            m_symbolToColIdx.begin(),
            m_symbolToColIdx.end(),
            std::back_inserter(keys),
            [](const decltype(m_symbolToColIdx)::value_type &pair){return pair.first;});
        return keys;
    }
    std::pair<IndexData::const_iterator,IndexData::const_iterator> getIndexRange(string start, string end) {
            time_t ts = utility::strTime2time_t(start.c_str());
            time_t te = utility::strTime2time_t(end.c_str());
            return getIndexRange(ts,te);
    }
    std::pair<IndexData::const_iterator,IndexData::const_iterator> getIndexRange(string end, int lagDays =28) {
            time_t te = utility::strTime2time_t(end.c_str());
            time_t ts = te - lagDays * 3600 * 24;
            // printf("end:%s; ts= %ld,te=%ld lagday=%d\n", end.c_str(),ts,te, lagDays);
            return getIndexRange(ts,te);
    }
    std::pair<IndexData::const_iterator,IndexData::const_iterator> getIndexRange(time_t start, time_t end) {
            time_t ts = start;
            time_t te = end;
            if (te < 105499200 || ts < 105499200 ) {
                printf("time range error ts:%ld,te:%ld\n",ts,te );
                throw std::runtime_error("Start time error");

            }
            int N  = m_index.size();
            auto posStart = m_index.end(); 
            auto posEnd = m_index.end();
            for (auto it = m_index.begin();it != m_index.end(); it++ ){
                // printf("ts:%ld,te:%ld,idx:%ld\n", ts,te, it->second);
                if (posStart == m_index.end() && it->second >= ts) {
                    posStart = it;
                }
                if (it->second >= te) {
                    posEnd = it;
                    break;
                }
            }
            if (posStart == m_index.end()) {
                throw std::runtime_error("Start time error");

            }
        return std::make_pair(posStart,posEnd);

    }
    const BigTable & read_csv( const std::string &filename) {
        using namespace csv;
        using namespace std;
        CSVFormat format;
        format.delimiter(',').no_header();

        CSVReader reader0(filename,format);
        auto  itRow = reader0.begin();
        vector<string> cols  ,symbols;
        string symbolPrev;
        int i = 0;
        for (auto itField = itRow->begin() +1 ; itField != itRow->end() ;itField ++ ){
            string symbol = itField->get<>();
            cols.push_back(symbol);
            if (symbolPrev != symbol) {
                symbols.push_back( itField->get<>());
                m_symbolToColIdx[symbol] = i;
            }
            symbolPrev  = symbol;
            i++;
        }
        itRow ++;
        i = 0;
        for (auto itField = itRow->begin() + 1; itField != itRow->end() ;itField ++ ){
            cols[i] = cols[i]  + "_"  + itField->get<>();
            m_columnData.push_back({cols[i] , std::vector<double> {}});
            i++;
        }
        format.column_names(cols);
        CSVReader reader(filename,format);
        itRow =  reader.begin();
        itRow ++;
        itRow ++;
        itRow ++;
        for(;itRow != reader.end(); itRow++ ) {
            auto itField = itRow->begin();
            string idx = itField->get<>();
            time_t t = utility::strTime2time_t(idx.c_str());
            m_index.push_back(make_pair(idx,t));
            int i = 0;
            for(itField++ ;itField != itRow->end(); itField++){
                //m_columnData[i++].second.push_back( itField->get<double>());
                string var = itField->get<>();
                double v = atof(var.c_str());
                m_columnData[i++].second.push_back(v);
            }
        }

        return *this;
    }

};
#endif 
