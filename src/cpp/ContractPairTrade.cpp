//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b

#include <sstream> // std::stringstream
#include <regex>
#include "contract.h"
#include "ContractPairTrade.h"
#include <execinfo.h>

using namespace std;

LogType Money::m_log = spdlog::stderr_color_mt("Money");
LogType ContractPairTrade::m_log = spdlog::stderr_color_mt("ContractPairTrade");

ContractPairTrade::ContractPairTrade (json &j ,  Money &m, std::string &slopeName) : m_money(&m),m_slopeName(slopeName) {
// ~/stock/env_study/2022-01-12.cn/js_coint.json
// {"pair":"BZUN_GDS","s_0":10.19418,"s_dayslr":4.71023,"s_daysfast":3.20328,
// "s_hllr":2.08931,"s_hlfast":3.24254,"std_rate":1.59872,"coint_days":14,
// "interval_secs":60.0,"he_0":0.32497,"hl_bars_0":116.92,
// "start":1640793540000,"end":1642003140000}

    //cout << coint_days << endl;
    try {
        j[m_slopeName].get_to(m_slope);
        int coint_days;
        j["coint_days"].get_to(coint_days);
        float std_rate, interval_secs, he_0, hl_bars_0;
        j["std_rate"].get_to(std_rate);
        //cout << std_rate << endl;
        j["interval_secs"].get_to(interval_secs);
        //cout << interval_secs << endl;
        j["he_0"].get_to(he_0);
        //cout << he_0 << endl;
        j["hl_bars_0"].get_to(hl_bars_0);
        //cout << hl_bars_0 << endl;
        //https://github.com/nlohmann/json/blob/develop/doc/examples/get_to.cpp
        string var;
        unsigned long  start,end;
        time_t m_start,m_end;
        j["start"].get_to(start);
        //cout << start << endl;
        //m_start = atoll(var.c_str()) / 1000;
        j["end"].get_to(end);
        //cout << end << endl;
        m_start = start /1000;
        m_end = end /1000;
        //m_end = atoll(var.c_str()) / 1000;

        j["pair"].get_to(var);
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
        m_log->debug("[{}_{}] {}_{} coint_days:{},std_rate:{}, interval_secs:{}, he_0:{}, hl_bars_0:{},slopeName:{},slope:{} ", m_n1, m_n2
                , m_start,m_end
                ,coint_days,std_rate, interval_secs, he_0, hl_bars_0
                ,m_slopeName, m_slope
                );
    }
    catch (nlohmann::detail::type_error &e) {
        void* callstack[128];
         int i, frames = backtrace(callstack, 128);
         char** strs = backtrace_symbols(callstack, frames);
         for (i = 0; i < frames; ++i) {
             printf("%s\n", strs[i]);
         }
         free(strs);
         exit(0);
    }

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

void ContractPairTrade::newPosition(float x, float y,bool buyN1, float z0, const time_t &t, const std::map<std::string, std::any> & ext) {
    m_openTime = t;
    //apply for $10000
    double amount = 10000;
    //use 100% margin rate
    int pos_y = round ((x < y) ? (amount /y) : (amount /x / m_slope) );
    int pos_x = round(pos_y * m_slope);
    if(buyN1) {
        pos_y *= -1;
    }
    else {
        pos_x *= -1;
    }
    auto cap_x = x * pos_x;
    auto cap_y = y * pos_y;
    auto totalCashPrev =  m_money->getTotalCash() ;
    auto totalMarginPrev =   m_money->getTotalMarginFreezed();
    if( !m_money->isMoneyAvailable(max(cap_x, cap_y), -min(cap_x, cap_y), 0.5,0.5)) {
        m_log->warn("C[{}];M[{}] Money is not enough. cap_x:{}, cap_y:{}"
        , totalCashPrev, totalMarginPrev
        ,cap_x, cap_y
        );
        return;
    }
    m_position1.m_position = pos_x;
    m_position2.m_position = pos_y;
    m_position1.m_avgprice = x;
    m_position2.m_avgprice = y;
    m_z0 = z0;
    m_money->withdraw(max(cap_x, cap_y), -min(cap_x, cap_y));

    auto totalCash =  m_money->getTotalCash() ;
    auto totalMargin =   m_money->getTotalMarginFreezed();
    m_log->warn("C:[{},{}];M:[{},{}]\t[{}_{}]:newPosition: x({}x{}={}),y({}x{}={}), slope:{}"
        ,totalCashPrev,totalCash,totalMarginPrev, totalMargin
        ,m_n1, m_n2
        ,x,pos_x,cap_x
        ,y,pos_y,cap_y
        ,m_slope
    );

}
float ContractPairTrade::closePosition(float x, float y, const time_t &t, const std::map<std::string, std::any> & ext) {
    m_closeTime = t;
    auto pos_x = m_position1.m_position;
    auto pos_y = m_position2.m_position;
    auto x0 = m_position1.m_avgprice ;
    auto y0 = m_position2.m_avgprice ;
    auto dx = x - x0;
    auto dy = y - y0;
    auto cap_x = x * pos_x;
    auto cap_y = y * pos_y;
    auto cap_x_d = dx * pos_x;
    auto cap_y_d = dy * pos_y;

    auto profit = dx * pos_x + dy * pos_y;

    auto totalCashPrev =  m_money->getTotalCash() ;
    auto totalMarginPrev =   m_money->getTotalMarginFreezed();

    auto commission = (abs(pos_x) + abs(pos_y)) * 0.01;
    if(pos_x >0){
        m_money->deposit(-commission + cap_x +cap_y_d, -pos_y *y0);
    }
    else {
        m_money->deposit(-commission +cap_y + cap_x_d, -pos_x *x0);
    }
    auto totalCash =  m_money->getTotalCash() ;
    auto totalMargin =   m_money->getTotalMarginFreezed();
    profit -= commission;
    addProfit( profit);

    

    m_log->warn("C:[{},{}];M:[{},{}]\t[{}_{}]:closePosition: (x:{} - x0:{}) * pos_x:{} = cap_x_d:{}; (y:{} - y0:{}) * pos_y:{} = cap_y_d:{}; slope:{} "
        ,totalCashPrev,totalCash,totalMarginPrev, totalMargin
        ,m_n1, m_n2
        ,x,x0,pos_x, cap_x_d
        ,y,y0,pos_y, cap_y_d
        ,m_slope
    );
    m_position1.m_position  = m_position2.m_position = 0;
    return profit;
}

#if 0
ContractPairTrade::ContractPairTrade (csv::CSVRow& row, Money &m) : m_money(&m) {
    // s,i,m,st,halflife,pair,p,pmin,ext
    m_slope  = row["s"].get<float>();
    m_intercept  = row["i"].get<float>();
    m_mean  = row["m"].get<float>();
    m_std  = row["st"].get<float>();
    m_halflife  = row["halflife"].get<float>() * 5 * 60;
    m_he  = row["HE"].get<float>();
    auto var  = row["pair"].get<>();
    m_name = var;
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
#endif
