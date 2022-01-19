//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include <regex>
#include <sstream> // std::stringstream
                   //
using namespace std;

class IContract{
public:
    virtual ~IContract( ) {}
};
class ContractPairTrade : public IContract {
public:
    ContractPairTrade (const std::vector<std::string> & colNames, const string &line) {
        std::stringstream ss(line);
        int i  = 0;
        std::string var;
        while(std::getline(ss, var, ','))
        {
            // s,i,m,st,halflife,pair,p,pmin,ext
            auto fName = colNames[i];
            char * end ;
            if (fName == "s" ) {
                m_slope  = std::strtof(var.c_str(),&end);
            }
            else if (fName == "i" ) {
                m_intercept  = std::strtof(var.c_str(),&end);
            }
            else if (fName == "m" ) {
                m_mean  = std::strtof(var.c_str(),&end);
            }
            else if (fName == "st" ) {
                m_std  = std::strtof(var.c_str(),&end);
            }
            else if (fName == "halflife" ) {
                m_halflife  = std::strtof(var.c_str(),&end);
            }
            else if (fName == "pair" ) {
                std::regex re(R"(.*)_(.*)");
                std::smatch pieces_match;
                bool ret = std::regex_match(var,pieces_match,re);
                assert(ret);
                assert(pieces_match.size() == 2);
                m_n1 = pieces_match[0].str();
                m_n2 = pieces_match[1].str();
                m_symbolsPair = std::make_pair(m_n1,m_n2);
            }
            else if (fName == "p" ) {
                m_p  = std::strtof(var.c_str(),&end);
            }
            else if (fName == "pmin" ) {
                m_pmin  = std::strtof(var.c_str(),&end);
            }
            else if (fName == "ext" ) {
                m_ext  = var;
            }
            else {
                throw std::runtime_error("Unkow field in file " + fName);
            }
            i++;

        }

    }
    std::vector<std::string>  getSymbols() const {
        std::vector<std::string> p  { m_symbolsPair.first,m_symbolsPair.second};
        return p;
    }
    void debug(LogType log) { log->debug("{}_{}:slope:{},intercept:{},mean:{},std:{},halflife:{},p:{},pmin:{},ext:{}", m_n1,m_n2, m_slope,m_intercept ,m_mean, m_std, m_halflife, m_p,m_pmin, m_ext); }
public:
    float m_slope,m_intercept ,m_mean, m_std, m_halflife, m_p,m_pmin;
    std::string m_ext, m_n1,m_n2;
private:
    std::pair<std::string, std::string> m_symbolsPair; 
    // s,i,m,st,halflife,pair,p,pmin,ext

};

