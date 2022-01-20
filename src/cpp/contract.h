//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include <regex>
#include <sstream> // std::stringstream

using namespace std;

class IContract{
public:
    virtual ~IContract( ) {}
};

class SnapData;
class ContractPairTrade : public IContract {
public:
    ContractPairTrade (csv::CSVRow& row) {
        // s,i,m,st,halflife,pair,p,pmin,ext
        m_slope  = row["s"].get<float>();
        m_intercept  = row["i"].get<float>();
        m_mean  = row["m"].get<float>();
        m_std  = row["st"].get<float>();
        m_halflife  = row["halflife"].get<float>();
        auto var  = row["pair"].get<>();
        //
        std::string reStr = "(.*)_(.*)";
        std::regex re(reStr);
        std::smatch pieces_match;
        bool ret = std::regex_match(var,pieces_match,re);
        if(!ret) {
            throw std::runtime_error("Regx match error " + var + " re: " + reStr);
        }
        assert(pieces_match.size() == 3);
        m_n1 = pieces_match[1].str();
        m_n2 = pieces_match[2].str();
        m_symbolsPair = std::make_pair(m_n1,m_n2);

        m_p  = row["p"].get<float>();
        m_pmin  = row["pmin"].get<float>();
        m_ext  = row["ext"].get<>();


    }
    std::vector<std::string>  getSymbols() const {
        std::vector<std::string> p  { m_symbolsPair.first,m_symbolsPair.second};
        return p;
    }
    bool  isAvailable() {return  m_isAvailable; }
    void debug(LogType log) { log->debug("available:{}; {}_{}:slope:{},intercept:{},mean:{},std:{},halflife:{},p:{},pmin:{},ext:{}",
            m_isAvailable,
            m_symbolsPair.first,m_symbolsPair.second, m_slope,m_intercept ,m_mean, m_std, m_halflife, m_p,m_pmin, m_ext); }

public:
    float m_slope,m_intercept ,m_mean, m_std, m_halflife, m_p,m_pmin;
    std::string m_ext, m_n1,m_n2;
    std::pair<std::string, std::string> m_symbolsPair; 
    // s,i,m,st,halflife,pair,p,pmin,ext
    std::vector<SnapData>::iterator  m_n1SnapData;
    std::vector<SnapData>::iterator   m_n2SnapData;
    bool m_isAvailable {false};
private:
};

