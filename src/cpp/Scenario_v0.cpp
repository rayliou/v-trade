//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#include "common.h"

#include "Scenario_v0.h"
#include <fstream>
#include <numeric>


using namespace std;

LogType Scenario_v0::m_log = spdlog::stderr_color_mt("Scenario_v0");
LogType Scenario_v0::m_out = spdlog::stdout_color_mt("stdout");

//https://stackoverflow.com/questions/18939869/how-to-get-the-slope-of-a-linear-regression-line-using-c
template<typename T>
T slope(const std::vector<T>& x, const std::vector<T>& y) {
    const auto n    = x.size();
    const auto s_x  = std::accumulate(x.begin(), x.end(), 0.0);
    const auto s_y  = std::accumulate(y.begin(), y.end(), 0.0);
    const auto s_xx = std::inner_product(x.begin(), x.end(), x.begin(), 0.0);
    const auto s_xy = std::inner_product(x.begin(), x.end(), y.begin(), 0.0);
    const auto a    = (n * s_xy - s_x * s_y) / (n * s_xx - s_x * s_x);
    return a;
}

Scenario_v0::Scenario_v0(const char * pairCsv, CmdOption &cmd, const char * conf) : IScenario(cmd), m_pairCsv(pairCsv)  {
        //m_log = spdlog::stderr_color_mt(typeid(*this).name());
        //m_log = spdlog::get("Scenario_v0");
    setupContractPairTrades(pairCsv);
    for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
        //if(c.isIgnored()) {
            //m_log->debug("Ignore symbol {}_{}", c.m_n1, c.m_n2);
            //return;
        //}
        auto symbols = c.getSymbols();
        for_each(symbols.begin(), symbols.end(), [&] (const string  & symbol ) {
                m_snapDataVector.push_back(SnapData(symbol) );
        });

    });
}
void Scenario_v0::debug(LogType *log) {
    if (nullptr == log) {
        log  = &m_log;
    }
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto &c ) {
            c.debug(m_log);
            if(c.isAvailable()) {
                c.m_snap1->debug(*log);
                c.m_snap2->debug(*log);
            }
    });
}
void Scenario_v0::setupContractPairTrades(const char *pairCsv) {
    using namespace csv;
    CSVReader reader(pairCsv);
    for (CSVRow& row: reader) {
        m_contracts.push_back(ContractPairTrade(row, m_money));
    }

}
void Scenario_v0::postSetup() {
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto & c ) {
        for(auto it = m_snapDataVector.begin(); it != m_snapDataVector.end(); it++) {
            if (c.m_n1 == it->symbol) {
                c.m_snap1 = &(*it);
            }
            if (c.m_n2 == it->symbol) {
                c.m_snap2 = &(*it);
            }

        }
    });
    auto isSnapAvailable  = []  (auto * ptr) -> bool { return ptr != nullptr && ptr->idx != -1;  };
    if ( m_includes.size() >0) {
        for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            auto it1 = m_includes.find(c.m_n1);
            auto it2 = m_includes.find(c.m_n2);
            auto available =  ( it1 != m_includes.end() && it2 != m_includes.end());
            available = available && isSnapAvailable(c.m_snap1) && isSnapAvailable(c.m_snap2);
            c.setAvailable(available);
        });
    }
    else if ( m_excludes.size() >0) {
        for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            auto it1 = m_excludes.find(c.m_n1);
            auto it2 = m_excludes.find(c.m_n2);
            auto available =  ( it1 == m_excludes.end() && it2 == m_excludes.end());
            available = available && isSnapAvailable(c.m_snap1) && isSnapAvailable(c.m_snap2);
            c.setAvailable(available);
        });
    }
    else {
        for(auto & c: m_contracts) {
            auto  available = isSnapAvailable(c.m_snap1) && isSnapAvailable(c.m_snap2);
            c.setAvailable(available);
        }
    }
    auto endIt = remove_if(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            bool ret =  !c.isAvailable();
            ret |= c.m_he > 0.45;
            ret |= c.m_halflife > 6 *3600;
            m_log->info("{}_{}:{}", c.m_n1, c.m_n2, (ret?"Remove unused":"Keep"));
            return ret;
    });
    m_contracts.erase(endIt,m_contracts.end());
}
void Scenario_v0::preOneEpoch(const std::map<std::string, std::any>& ext) {
}
void Scenario_v0::postOneEpoch(const std::map<std::string, std::any>& ext) {

    vector<IContract *> contracts;
    for (auto &c:m_contracts ) {
        auto p  = c.getProfit();
        if(p == 0) {
            continue;
        }
        contracts.push_back(&c);
    }
    // transform(m_contracts.begin(),m_contracts.end(),back_inserter(contracts),[&] (auto & c ) -> auto { return &c; });
    sort(contracts.begin(),contracts.end(), [&] (IContract *aC, IContract *bC) -> auto {
        auto a  = aC->getProfit();
        auto b  = bC->getProfit();
        if (a == b) {
            return aC->getName() < bC->getName();
        }
        if ( a == 0){
            return true;
        }
        if ( b == 0){
            return false;
        }
        return a <b;
    });
    for (auto c :contracts ) {
        ContractPairTrade *p = dynamic_cast<ContractPairTrade *>(c);
        int duration = p->getTransDuration();
        int halflife = p->m_halflife ;
        m_out->info("[{}]\tTrans:{},profit:{:.2f}\tP:{:04.2f},Pmin:{:04.2f},HE:{:04.2f}\tduration: {:1d} mins, halflife:{:1d} mins", p->getName(),p->getTransactionNum(), p->getProfit()
        ,p->m_p,p->m_pmin, p->m_he
        , duration/60, halflife/60
        //, p->m_ext
        );
    }
    // for_each(m_contracts.begin(),m_contracts.end(),[&] (auto & c ) {
    //     m_log->debug("[{}_{}] Profit:{} " , c.m_n1,c.m_n2, c.getProfit());
    // });
    vector<float> v;
    transform(contracts.begin(),contracts.end(), back_inserter(v),  [&] (auto & c ) {
        return c->getProfit();
    });
    auto sum = std::accumulate(v.begin(), v.end(), 0.0);
    auto mean = sum / v.size();
    auto sq_sum = std::inner_product(v.begin(), v.end(), v.begin(), 0.0);
    auto stdev = std::sqrt(sq_sum / v.size() - mean * mean);
    m_out->info("Total:{}, mean: {}, std:{},sum:{}", v.size(),mean, stdev, sum);

}
void Scenario_v0::runOneEpoch(const std::pair<std::string, time_t>  & cur,const std::pair<std::string, time_t>  & start ) {
    //return;
    auto secsFromStart = cur.second - start.second;
    int forceCloseTime = start.second + 3600 * 3; //3hrs
    //int daysAfterStart = secsFromStart/(3600 * 24);
    std::map<std::string, std::any>  ext;
    ext["start"] = start;
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto &c ) {
            auto transactionNum = c.getTransactionNum();
            //if (!c.isAvailable()) { return; }
            if(transactionNum >= 1) {
                //do nothing
                m_log->debug("{}:{} Reach out of the max transaction num:{} " ,cur.first, c.getName(), transactionNum);
                return;
            }
            auto x = c.m_snap1->close;
            auto y = c.m_snap2->close;
            auto diff = x * c.m_slope + c.m_intercept - y;
            c.m_z = (diff - c.m_mean)/c.m_std;
            m_log->debug("[{}][{}_{}] Start strategy test  z:{}, zPrev:{} x:{},y:{}, slope/intercept:{},{},mean:{},std:{}" , cur.first,
                    c.m_n1,c.m_n2, c.m_z, c.m_zPrev, x,y, c.m_slope, c.m_intercept,c.m_mean, c.m_std);
            if (c.m_position1.m_position != 0 ) { //holding a position
                if (cur.second > forceCloseTime ) {
                    m_log->warn("next day Close position {}_{} {} {} " , c.m_n1,c.m_n2, x,y);
                     c.closePosition(x,y,cur.second,ext);
                }
                else if (c.getHoldingTime(cur.second) > c.m_halflife ) {
                    m_log->warn("[{}][{}] close position due to timeout of halflife {}", cur.first, c.getName(), c.m_halflife);
                     c.closePosition(x,y,cur.second,ext);
                }
                else { 
                    auto z0 = c.m_z0;
                    auto z = c.m_z;
                    auto zPrev = c.m_zPrev;
                    bool isProfit = (z0 <0 )? ( z> z0): ( z <z0);
                    bool isNearer = (z0 <0 )? ( z> zPrev): ( z <zPrev);
                    auto zdiff = abs(z-z0);
                    auto zdiffPrev = abs(zPrev-z0);

                    m_log->debug("isProfit,isNearer,zdiff,zdiffPrev:{} {} {} {}", isProfit,isNearer,zdiff,zdiffPrev);
                    if (isNearer) { //-> near
                        m_log->debug("[{}_{}] Trail: let it go.  z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0); 
                    }
                    else { //-> far
                        if(isProfit) {
                            if (abs(zPrev -z0)> 1.3  ) {
                                m_log->warn("[-{}_+{}] Wow profit close Position z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0);
                                c.closePosition(x,y,cur.second,ext);
                            }
                        else { //wait for the profit point
                            m_log->debug("[{}_{}] Wait for the profit point z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0); 
                        }
                        }
                        else { //uder loss state
                            if (zdiff > 1.0 && !isProfit) { //cut loss
                                m_log->warn("[-{}_+{}] Stop loss close Position z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0);
                                c.closePosition(x,y,cur.second,ext);
                            }
                            else { //draw down
                                m_log->debug("[{}_{}] Drawdown. maybe increase position z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0); 
                            }
                        }


                    }

                }
            }
            else {
                if (cur.second > forceCloseTime ) {
                    return;
                }
                else {
                    if( (c.m_zPrev <0 && c.m_z < c.m_zPrev ) || ( c.m_zPrev >0 && c.m_z > c.m_zPrev ) ) {
                        m_log->debug("[{}_{}] Trail far z:{}, zPrev:{} " , c.m_n1,c.m_n2, c.m_z, c.m_zPrev);
                    }
                    else if ( c.m_z < -2.0) {
                        m_log->warn("[+{}_-{}] new Position z:{}, zPrev:{} " , c.m_n1,c.m_n2, c.m_z, c.m_zPrev);
                        c.newPosition(x,y,true,c.m_z,cur.second, ext);
                    }
                    else if ( c.m_z > 2.0) {
                        m_log->warn("[-{}_+{}] new Position z:{}, zPrev:{} " , c.m_n1,c.m_n2, c.m_z, c.m_zPrev);
                        c.newPosition(x,y,false,c.m_z,cur.second, ext);
                    }
                    else {
                        m_log->debug("[{}_{}] Do nothing  z:{}, zPrev:{} " , c.m_n1,c.m_n2, c.m_z, c.m_zPrev);
                    }
                }

            }
            c.m_zPrev = c.m_z;
    });

}
