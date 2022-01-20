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
                   //
using namespace std;

using IndexData =  vector<pair<string,time_t>>;
using ColumnData = vector<pair<std::string, std::vector<double>>>;
using SymbolToColIdx = map<string,int>;
using TableData = tuple<SymbolToColIdx,IndexData,ColumnData>;


class BigTable{

public:
    const char * TIME_FORMAT = "%Y-%m-%d %H:%M:%S";
    int m_fieldsNum {5};
    IndexData m_index;
    ColumnData m_columnData;
    SymbolToColIdx m_symbolToColIdx;

    BigTable(const char *csvPath) {
        this->read_csv(csvPath);
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
            struct tm timeptr;
            strptime(start.c_str(),TIME_FORMAT,&timeptr);
            time_t ts = mktime(&timeptr);
            strptime(end.c_str(),TIME_FORMAT,&timeptr);
            time_t te = mktime(&timeptr);
            return getIndexRange(ts,te);
    }
    std::pair<IndexData::const_iterator,IndexData::const_iterator> getIndexRange(string end, int lagDays =28) {
            struct tm timeptr;
            strptime(end.c_str(),TIME_FORMAT,&timeptr);
            time_t te = mktime(&timeptr);
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

        std::ifstream myFile(filename);
        // Make sure the file is open
        if(!myFile.is_open()) throw std::runtime_error("Could not open file");
        // Helper vars
        std::string line, colname;
        // Read the column names
        vector<string> columns, symbols; 
        if(myFile.good())
        {
            // Extract the first line in the file
            std::getline(myFile, line);
            // Create a stringstream from line
            std::stringstream ss(line);
            std::getline(ss, colname, ',');
            assert( colname == "");
            // Extract each column name
            string symbolsPrev;
            int i = 0;
            while(std::getline(ss, colname, ','))
            {
                columns.push_back(colname);
                if (colname != symbolsPrev)
                {
                    symbols.push_back(colname);
                    m_symbolToColIdx[colname] = i;
                    i++;
                }
                symbolsPrev = colname;
            }
        }
        if(myFile.good())
        {
            // Extract the 2nd line in the file
            std::getline(myFile, line);
            // Create a stringstream from line
            std::stringstream ss(line);
            std::getline(ss, colname, ',');
            assert( colname == "");
            // Extract each column name
            int i = 0;
            while(std::getline(ss, colname, ','))
            {
                columns[i] = columns[i] + '_'+ colname;
                //cout << columns[i] << endl;
                // colum data
                m_columnData.push_back({columns[i] , std::vector<double> {}});
                i++;
            }
            // Extract the 3rd line in the file
            std::getline(myFile, line);
        }
        //cout << "xxxxxxxxx" << endl;

        // Read data, line by line
        // from the 4th line
        string idx;
        while(std::getline(myFile, line))
        {
            std::stringstream ss(line);
            std::getline(ss, idx, ',');
            struct tm timeptr;
            strptime(idx.c_str(),TIME_FORMAT,&timeptr);
            time_t t = mktime(&timeptr);
            m_index.push_back(make_pair(idx,t));
            //cout << "idx: " << idx << endl;
            int colIdx = 0;
            string  strVal;
            while(std::getline(ss, strVal, ',')){
                double v = -999999;
                if (strVal != ""){
                    v = std::stod(strVal);
                }
                //cout << strVal << " to "  << v << endl;
                m_columnData.at(colIdx).second.push_back(v);
                colIdx++;
            }
        }

        // Close file
#if 0
        myFile.close();
        auto & r = columnData.at(2);
        cout << r.first << endl;
        for (auto &v : r.second){
            cout << v << endl;
        }
#endif
        return *this;
        //return TableData({});
        LogType m_log { spdlog::stdout_color_mt("BigTable")};
    }

};
