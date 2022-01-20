//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include <any> // std::stringstream
#include <sstream> // std::stringstream
#include <regex>
#include "contract.h"

class SnapData;
class ContractPairTrade : public IContract {
public:
    ContractPairTrade (csv::CSVRow& row);
    std::vector<std::string>  getSymbols() const;
    bool  isAvailable() {return  m_isAvailable; }
    void debug(LogType log) ;
    void newPosition(float x, float y, bool buyN1, const std::map<std::string, std::any> &ext);
    float  closePosition(float x, float y, const std::map<std::string, std::any> & ext);

public:
    float m_slope,m_intercept ,m_mean, m_std, m_halflife, m_p,m_pmin;
    float m_z {0};
    float m_zPrev {0};
    float m_z0 {0};
    std::string m_ext, m_n1,m_n2;
    std::pair<std::string, std::string> m_symbolsPair; 
    // s,i,m,st,halflife,pair,p,pmin,ext
    std::vector<SnapData>::iterator  m_n1SnapData;
    std::vector<SnapData>::iterator   m_n2SnapData;
    Position m_position1;
    Position m_position2;
    bool m_isAvailable {false};
private:
    ContractPairTrade () = delete;
private:
    static LogType  m_log;
};

