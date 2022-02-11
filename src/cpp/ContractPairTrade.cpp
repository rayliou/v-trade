//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b

#include <sstream> // std::stringstream
#include <regex>
#include "contract.h"
#include "ContractPairTrade.h"
#include <execinfo.h>
#include <tuple>

using namespace std;

LogType Money::m_log = spdlog::stderr_color_mt("Money");
LogType ContractPairTrade::m_log = spdlog::stderr_color_mt("ContractPairTrade");

ContractPairTrade::ContractPairTrade (json &j ,  Money &m, std::string &slopeName) : m_money(&m),m_slopeName(slopeName) {
    float MAX_SLOPE_DIFF_RATE = 0.3;
    const int MIN_HALFLIFE_SECS = 34 *60;
    const float MAX_PVALUE = 0.1;
// ~/stock/env_study/2022-01-12.cn/js_coint.json
// {"pair":"BZUN_GDS","s_0":10.19418,"s_dayslr":4.71023,"s_daysfast":3.20328,
// "s_hllr":2.08931,"s_hlfast":3.24254,"std_rate":1.59872,"coint_days":14,
// "interval_secs":60.0,"he_0":0.32497,"hl_bars_0":116.92,
// "start":1640793540000,"end":1642003140000}

    //cout << coint_days << endl;
#if 0
    try {
        j[m_slopeName].get_to(m_slope);
        list<float> slopes;
        float s;
        j["s_0"].get_to(s);
        slopes.push_back(s);
        j["s_dayslr"].get_to(s);
        slopes.push_back(s);
        j["s_daysfast"].get_to(s);
        slopes.push_back(s);
        j["s_hllr"].get_to(s);
        slopes.push_back(s);
        j["s_hlfast"].get_to(s);
        slopes.push_back(s);
        slopes.sort();
        slopes.pop_back();
        slopes.pop_front();
        m_slope = std::accumulate(slopes.begin(), slopes.end(), 0.0)/slopes.size();
#endif
        float s_0, s_dayslr;
        j["s_0"].get_to(s_0);
        j["s_dayslr"].get_to(s_dayslr);
        m_slopeDiffRate = fabs( (s_0 - s_dayslr)/s_dayslr) ;
        m_slope = m_slopeDiffRate <=  MAX_SLOPE_DIFF_RATE ? s_dayslr : 0.;


        j["coint_days"].get_to(coint_days);


        j["std_rate"].get_to(std_rate);
        //cout << std_rate << endl;
        j["interval_secs"].get_to(interval_secs);
        //cout << interval_secs << endl;
        j["he_0"].get_to(he_0);
        //cout << he_0 << endl;
        j["hl_bars_0"].get_to(hl_bars_0);
        halflifeSecs =  hl_bars_0 * interval_secs;
        if (halflifeSecs < MIN_HALFLIFE_SECS) {
            m_slope = 0;
        }
        j["pxy"].get_to(m_pxy);
        j["pyx"].get_to(m_pyx);
        j["mean0"].get_to(m_mean0);
        j["std0"].get_to(m_std0);

        if(m_pxy > MAX_PVALUE || m_pyx > MAX_PVALUE) { m_slope = 0; }

        //cout << hl_bars_0 << endl;
        //https://github.com/nlohmann/json/blob/develop/doc/examples/get_to.cpp
        string var;
        unsigned long  start,end;
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
        m_name = var;
        m_symbolsPair = std::make_pair(m_n1,m_n2);
        m_log->debug("[{}_{}] {}_{} coint_days:{},std_rate:{}, interval_secs:{}, he_0:{}, hl_bars_0:{},slopeName:{},slope:{} ", m_n1, m_n2
                , m_start,m_end
                ,coint_days,std_rate, interval_secs, he_0, hl_bars_0
                ,m_slopeName, m_slope
                );
#if 0
    }
    catch (exception &e) {
        cout << e.what() << endl;
        void* callstack[128];
         int i, frames = backtrace(callstack, 128);
         char** strs = backtrace_symbols(callstack, frames);
         for (i = 0; i < frames; ++i) {
             printf("%s\n", strs[i]);
         }
         free(strs);
         exit(0);
    }
#endif

}
std::vector<std::string>  ContractPairTrade::getSymbols() const {
    std::vector<std::string> p  { m_symbolsPair.first,m_symbolsPair.second};
    return p;
}
void ContractPairTrade::debug(LogType log) {
    log->debug("available:{}; {}_{}:slope:{},intercept:{},mean:{},std:{},pxy:{},pyx:{},ext:{}",
        m_isAvailable,
        m_symbolsPair.first,m_symbolsPair.second, m_slope,m_intercept ,m_mean, m_std,m_pxy, m_pyx, m_ext); 
}

void ContractPairTrade::addLongDiffItem(DiffDataBase &b) {
    m_longWindowDiff.push_back(b);
}
void ContractPairTrade::initWindowByHistory(WinDiffDataType &&winDiff) {
    auto i = 0;
    auto totalCnt = winDiff.size();
    for(auto &d : winDiff) {
        this->updateEMA(d);
        d.mean0 = m_mean0;
        d.std0 = m_std0;
        d.debug(m_log, i++, totalCnt,m_name); 
        m_winDiff.push_back(d,false);

    }
    m_log->debug("[{}]:Set m_winDiff.size:{}",m_name, m_winDiff.size());
}
void  ContractPairTrade::updateLongWindow(DiffData &diffData) {
    //cal mean0 & std0
    this->addLongDiffItem(diffData);
    auto start = diffData.tm - (m_end - m_start);
    auto endIt = remove_if(m_longWindowDiff.begin(),m_longWindowDiff.end(), [&] (DiffDataBase & b ) {
        return b.tm < start;
    });
    // items removed has benn moved after the main list.
    m_longWindowDiff.erase(endIt,m_longWindowDiff.end());
    // m_log->debug( "begin:{}, start:{}, cur:{}", m_longWindowDiff.begin()->tm, start, diffData.tm);
    // using SumTuple=tuple<float,float>;
    // SumTuple  sumTuple {0., 0.};
    float sum = 0;
    sum = std::accumulate(m_longWindowDiff.rbegin(),m_longWindowDiff.rend(), sum, [&](const auto & a, const auto &b) -> float {
        return a+b.diff;
    });
    diffData.mean0 = sum/m_longWindowDiff.size();
    sum = std::accumulate(m_longWindowDiff.rbegin(),m_longWindowDiff.rend(), 0, [&](const auto & a, const auto &b) -> float {
        auto d = b.diff - diffData.mean0;
        return a+ d * d;
    });
    diffData.std0 = std::sqrt(sum /(m_longWindowDiff.size()-1));
    return;
}
void  ContractPairTrade::updateEMA(DiffData &diffData) {
    int size = m_winDiff.size();
    int m_lookBackHalf = round(this->getLookBackBars() /2);
    int m_lookBackQuarter = round(m_lookBackHalf /2);
    int lookBack5Bars = 5;
    m_lookBackQuarter  = m_lookBackQuarter <5  ? 5: m_lookBackQuarter ;
    m_lookBackHalf     = m_lookBackHalf <5  ? 5: m_lookBackHalf ;
    //FIXME weight.
    if (m_winDiff.size() == 0) {
        diffData.ema = diffData.diff;
        diffData.ema_half = diffData.diff;
        diffData.ema_quarter = diffData.diff;
        diffData.ema_5bars = diffData.diff;
        return;
    }
    auto calEMA = [&] (int lookBack, float spread, float ema, float var) -> pair<float, float> {
        float L = 2.0/(1+lookBack);
        float ema1 = L * spread + (1-L) * ema ;
        float var1 = L * (spread - ema)*(spread - ema) + (1-L) * var;
        m_log->trace("calEMA:L={},spread={},ema0={}, em1={}; var0:{}, var1:{} ", L, spread, ema, ema1, var, var1);
        return make_pair(ema1, var1);
    };
    auto prev = m_winDiff.rbegin();
    float v = diffData.diff - prev->diff;
    v *= v;

    auto ema_var = calEMA(getLookBackBars(), diffData.diff, prev->ema, prev->em_var);
    diffData.ema = ema_var.first;
    diffData.em_var = (1 == size) ? v : ema_var.second;

    ema_var = calEMA(m_lookBackHalf, diffData.diff, prev->ema_half, prev->em_var_half);
    diffData.ema_half = ema_var.first;
    diffData.em_var_half = (1 == size) ? v : ema_var.second;

    ema_var = calEMA(m_lookBackQuarter, diffData.diff, prev->ema_quarter, prev->em_var_quarter);
    diffData.ema_quarter = ema_var.first;
    diffData.em_var_quarter = (1 == size) ? v : ema_var.second;

    ema_var = calEMA(lookBack5Bars, diffData.diff, prev->ema_5bars, prev->em_var_5bars);
    diffData.ema_5bars = ema_var.first;
    diffData.em_var_5bars = (1 == size) ? v : ema_var.second;
    return;
}
WinDiffDataType &  ContractPairTrade::updateWindowBySnap(DiffData &diffData,std::ostream *pOut ) {
    updateLongWindow(diffData);
    updateEMA(diffData);
    if (m_winDiff.size() >  getLookBackBars()) {
        m_winDiff.pop_front();
    }
    //cal mean & std
    m_winDiff.push_back(diffData,true);
    using SumPair=pair<float,float>;
    SumPair  sumPair {0., 0.};
    int cnt = 0;
    int sizeHalf = m_winDiff.size()/2;
    //reverse sum and sum half.
    sumPair = std::accumulate(m_winDiff.rbegin(),m_winDiff.rend(), sumPair, [&](const SumPair  & a, const auto &b) -> SumPair {
        auto [s0,s1] = a;
        s0 += b.diff;
        cnt++;
        if(cnt <= sizeHalf) {
            s1 += b.diff;
        }
        return make_pair(s0,s1);
    });
    auto mean = sumPair.first/m_winDiff.size();
    auto last = m_winDiff.rbegin();
    last->mean = mean;
    last->mean_half = sumPair.second/sizeHalf;
    //std_s
    auto std2 = std::accumulate(m_winDiff.begin(),m_winDiff.end(), 0.0, [&](float  a, auto &b) -> float {
        auto d = b.diff - mean;
        return a + d *d;
    });
    std2 /= (m_winDiff.size() -1);
    std2 = std::sqrt(std2);
    last->std = std2;

    float d = getSpread();
    float m = getSpreadMean();
    float s = getSpreadStd();
    last->z   = (d-m)/s;
    m_log->trace("{}:z:{}= ({}-{})/{}", m_name, last->z, d, m, s);

    using SumTuple=tuple<float,float,float>;
    SumTuple  sumTuple {0., 0., 0.};
    cnt = 0;
    int cnt5 = 0;
    int cnt10 = 0;
    int cnt20 = 0;
    sumTuple = std::accumulate(m_winDiff.rbegin(),m_winDiff.rend(), sumTuple, [&](const SumTuple  & a, const auto &b) -> SumTuple {
        auto [s5,s10,s20] = a;
        cnt++;
        if (b.std > 0) {
            if(cnt <= 5) {
                s5 += b.std;
                cnt5++;
            }
            if(cnt <= 10) {
                s10 += b.std;
                cnt10++;
            }
            if(cnt <= 20) {
                s20 += b.std;
                cnt20++;
            }
        }
        return make_tuple(s5,s10,s20);
    });
    last->sm_std_5   = std::get<0>(sumTuple)/cnt5;
    last->sm_std_10   = std::get<1>(sumTuple)/cnt10;
    last->sm_std_20   = std::get<2>(sumTuple)/cnt20;
    auto last2 =  last;
    last2 ++;
    last->stdH   = std::max(last2->stdH,last->std);
    last->stdL   = std::min(last2->stdL,last->std);
    last->diffH   = std::max(last2->diffH,last->diff);
    last->diffL   = std::min(last2->diffL,last->diff);
    auto it  = m_winDiff.rbegin();
    cnt = 0;
    float diffPrev  = it->diff;
    float sumDD = 0.;
    //from N-1 to N-5
    for (cnt=0, it++ ; cnt < 5 && it != m_winDiff.rend();cnt++, it++) {
        sumDD += fabs(it->diff - diffPrev);
        diffPrev = it->diff;
    }
    last->avg_diffdiff  = sumDD /cnt;
    // last->debug(m_log, m_cntWinDiff,m_cntWinDiff , m_name);
    m_cntWinDiff++;
    if (pOut != nullptr) {
        *pOut << m_n1 << "*" << m_slope << '-' << m_n2 << ',' ;
        last->outValues(*pOut);
        *pOut << endl;
    }
    return m_winDiff;
#if 0
    auto add = [](float a, float b) -> float {
        return a +b;
    };
    auto multiple = [](auto & a , auto &b) -> float {
        return a.diff * b.diff;
    };
    auto sq_sum = std::inner_product(m_winDiff.begin(), m_winDiff.end(), m_winDiff.begin(), 0.0, add, multiple);
    auto stdev = std::sqrt(sq_sum / m_winDiff.size() - mean * mean);
    last->std = stdev;
    //FIXME generate signal
    m_log->debug("std: {} ,std2: {}, (std1-std2)/std2 rate: {} ", last->std, std2, (last->std-std2)/std2 * 100);
#endif
}
std::ostream & ContractPairTrade::outWinDiffDataValues(std::ostream & out) {
    for(auto & d: m_winDiff) {
        out << m_name << ",";
        d.outValues(out);
        out << endl;
    }
    return out;
}
void ContractPairTrade::newPosition(int direction, float profitCap, float x, float y) {
    m_hasCrossedStd_near =false;
    m_hasCrossedStd_far =false;
    m_hasCrossedStd_far2 =false;
    m_hasCrossedStd_far3 =false;

    m_hasCrossedMean = false;
    m_hasCrossedMean_half = false;
    m_diffFarest = 0.;
    // -1 too low, buy n1 & sell n2
    // 1 too high, buy n2 & sell n1
    auto last = m_winDiff.rbegin();
    m_openTime = last->tm;
    //apply for $10000
    double amount = 10000;
#if 0
    amount *= (m_moneyCoeff/std_rate);
#endif
    //use 100% margin rate
    //base on y
    int pos_y = round(amount /y);
    int pos_x = round(pos_y * m_slope);
    if (pos_x *x  > amount) {
        pos_x = round(amount /x);
        pos_y = round(pos_x/m_slope);
    }
    if(direction > 0) {
        pos_x *= -1;
    }
    else {
        pos_y *= -1;
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
    m_money->withdraw(max(cap_x, cap_y), -min(cap_x, cap_y));

    auto totalCash =  m_money->getTotalCash() ;
    auto totalMargin =   m_money->getTotalMarginFreezed();
    m_profitCap = profitCap;
    m_log->warn("C:[{},{}];M:[{},{}]\t[{}_{}]:newPosition: x({}x{}={}),y({}x{}={}), slope:{},diff~cap: [{}~{}]"
        ,totalCashPrev,totalCash,totalMarginPrev, totalMargin
        ,m_n1, m_n2
        ,x,pos_x,cap_x
        ,y,pos_y,cap_y
        ,m_slope
        ,last->diff,m_profitCap
    );

}
void ContractPairTrade::newPosition(float x, float y,bool buyN1, float z0, const time_t &t, const std::map<std::string, std::any> & ext) {
#if 0
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
#endif

}
float ContractPairTrade::getPnL(float x, float y) {
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
    auto commission = (abs(pos_x) + abs(pos_y)) * 0.01;
    profit -= commission;
    return profit;
}
float ContractPairTrade::closePosition(float x, float y) {
    // -1 too low, buy n1 & sell n2
    // 1 too high, buy n2 & sell n1
    auto profit = getPnL(x,y);

    auto last = m_winDiff.rbegin();
    m_closeTime = last->tm;
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
    addProfit( profit);
    m_log->warn("C:[{},{}];M:[{},{}]\t[{}_{}]:closePosition: (x:{} - x0:{}) * pos_x:{} = cap_x_d:{}; (y:{} - y0:{}) * pos_y:{} = cap_y_d:{}; slope:{},profit:{} "
        ,totalCashPrev,totalCash,totalMarginPrev, totalMargin
        ,m_n1, m_n2
        ,x,x0,pos_x, cap_x_d
        ,y,y0,pos_y, cap_y_d
        ,m_slope,profit
    );
    m_position1.m_position  = m_position2.m_position = 0;
    return profit;
}
float ContractPairTrade::closePosition(float x, float y, const time_t &t, const std::map<std::string, std::any> & ext) {
#if 0
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
#endif
    return 0;

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
