//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b

#include <sstream> // std::stringstream
#include <regex>
#include "contract.h"
#include "ContractPairTrade.h"

using namespace std;

LogType ContractPairTrade::m_log = spdlog::stdout_color_mt("ContractPairTrade");
ContractPairTrade::ContractPairTrade (csv::CSVRow& row) {
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
std::vector<std::string>  ContractPairTrade::getSymbols() const {
    std::vector<std::string> p  { m_symbolsPair.first,m_symbolsPair.second};
    return p;
}
void ContractPairTrade::debug(LogType log) {
    log->debug("available:{}; {}_{}:slope:{},intercept:{},mean:{},std:{},halflife:{},p:{},pmin:{},ext:{}",
        m_isAvailable,
        m_symbolsPair.first,m_symbolsPair.second, m_slope,m_intercept ,m_mean, m_std, m_halflife, m_p,m_pmin, m_ext); 
}

void ContractPairTrade::newPosition(float x, float y,bool buyN1, const std::map<std::string, std::any> & ext) {
    auto & pos2  = m_position2.m_position = 100;
    auto & pr2  = m_position2.m_avgprice = y;
    auto & pos1 = m_position1.m_position  = m_position2.m_position  * m_slope;
    auto & pr1 = m_position1.m_avgprice = x;
    if (buyN1) { m_position2.m_position *= -1; }
    else {m_position1.m_position *= -1;}
    m_log->warn("[{}_{}]:newPosition: x({},{}),y({},{})",m_n1, m_n2, pr1,pos1, pr2,pos2 );
}
float ContractPairTrade::closePosition(float x, float y, const std::map<std::string, std::any> & ext) {
    auto & pos2  = m_position2.m_position;
    auto  diff2  = y - m_position2.m_avgprice;
    auto & pos1 = m_position1.m_position;
    auto  diff1 = x-  m_position1.m_avgprice ;
    auto profit = diff1 * pos1 + diff2 * pos2;
    m_profit += profit;
    m_log->warn("[{}_{}]:ClosePosition:profit:{};  X:(pos:{},d:{},p0:{},p:{} ),Y:(pos:{},d:{},p0:{},p:{} )    ",m_n1, m_n2, profit
            ,pos1, diff1, m_position1.m_avgprice,x
            ,pos2, diff2, m_position2.m_avgprice,y
            );
    m_position1.m_position  = m_position2.m_position = 0;
    return profit;
}

