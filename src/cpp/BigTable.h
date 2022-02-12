//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
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
    const   char * TIME_FORMAT = "%Y-%m-%d %H:%M:%S";

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
            time_t ts = strTime2time_t(start.c_str());
            time_t te = strTime2time_t(end.c_str());
            return getIndexRange(ts,te);
    }
    std::pair<IndexData::const_iterator,IndexData::const_iterator> getIndexRange(string end, int lagDays =28) {
            time_t te = strTime2time_t(end.c_str());
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
            time_t t = strTime2time_t(idx.c_str());
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
public:
    time_t strTime2time_t(const char *s, const char *fmt=nullptr) {
        if (nullptr == fmt) {
            fmt = TIME_FORMAT;
        }
        struct tm timeptr;
        strptime(s,fmt,&timeptr);
        return mktime(&timeptr);
    }

};
