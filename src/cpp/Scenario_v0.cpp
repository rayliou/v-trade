//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#include "common.h"

#include "Scenario_v0.h"
#include <fstream>
#include <numeric>


using namespace std;

Scenario_v0::Scenario_v0(const char * pairCsv, CmdOption &cmd, const char * conf) : IScenario(cmd), m_pairCsv(pairCsv)  {
        m_log = spdlog::stdout_color_mt(typeid(*this).name());
    //m_log = spdlog::stdout_color_mt("Scenario_v0");
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
    if ( m_includes.size() >0) {
        for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            auto it1 = m_includes.find(c.m_n1);
            auto it2 = m_includes.find(c.m_n2);
            auto available =  ( it1 != m_includes.end() && it2 != m_includes.end());
            available = available && c.m_snap1 != nullptr && c.m_snap2 != nullptr;
            c.setAvailable(available);
        });
    }
    else if ( m_excludes.size() >0) {
        for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            auto it1 = m_excludes.find(c.m_n1);
            auto it2 = m_excludes.find(c.m_n2);
            auto available =  ( it1 == m_excludes.end() && it2 == m_excludes.end());
            available = available && c.m_snap1 != nullptr && c.m_snap2 != nullptr;
            c.setAvailable(available);
        });
    }
    else {
        for(auto & c: m_contracts) {
            auto  available = c.m_snap1 != nullptr && c.m_snap2 != nullptr;
            c.setAvailable(available);
        }
    }
    auto endIt = remove_if(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            bool ret =  !c.isAvailable();
            m_log->info("{}_{}:{}", c.m_n1, c.m_n2, (ret?"Remove unused":"Keep"));
            return ret;
    });
    m_contracts.erase(endIt,m_contracts.end());
    m_profits.clear();
}
void Scenario_v0::preOneEpoch(const std::map<std::string, std::any>& ext) {
}
void Scenario_v0::postOneEpoch(const std::map<std::string, std::any>& ext) {


    vector<pair<string,int>> contracts;
    transform(m_contracts.begin(),m_contracts.end(),back_inserter(contracts),[&] (auto & c ) -> auto {
        return make_pair(c.m_n1 + "_" +c.m_n2, c.getProfit());
    });
    sort(contracts.begin(),contracts.end(), [&] (auto & a, auto & b ) -> auto {
        if ( a.second == b.second) {
            return a.first < b.first;
        }
        if ( a.second == 0){
            return true;
        }
        if ( b.second == 0){
            return false;
        }
        return a.second < b.second;
    });
    for_each(contracts.begin(),contracts.end(), [&] (auto & c ) {
        m_log->info("[{}] Profit:{} " , c.first,c.second);
    });
    // for_each(m_contracts.begin(),m_contracts.end(),[&] (auto & c ) {
    //     m_log->debug("[{}_{}] Profit:{} " , c.m_n1,c.m_n2, c.getProfit());
    // });
    auto &v = m_profits;
    auto sum = std::accumulate(v.begin(), v.end(), 0.0);
    auto mean = sum / v.size();
    auto sq_sum = std::inner_product(v.begin(), v.end(), v.begin(), 0.0);
    auto stdev = std::sqrt(sq_sum / v.size() - mean * mean);
    m_log->info("Total:{}, mean: {}, std:{},sum:{}", v.size(),mean, stdev, sum);

}
void Scenario_v0::runOneEpoch(const std::pair<std::string, time_t>  & cur,const std::pair<std::string, time_t>  & start ) {
    //return;
    auto secsFromStart = cur.second - start.second;
    int forceCloseTime = start.second + 3600 * 3; //3hrs
    //int daysAfterStart = secsFromStart/(3600 * 24);
    std::map<std::string, std::any>  ext;
    ext["start"] = start;
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto &c ) {
            //if (!c.isAvailable()) { return; }
            auto x = c.m_snap1->close;
            auto y = c.m_snap2->close;
            auto diff = x * c.m_slope + c.m_intercept - y;
            c.m_z = (diff - c.m_mean)/c.m_std;
            m_log->debug("[{}][{}_{}] Start strategy test  z:{}, zPrev:{} x:{},y:{}, slope/intercept:{},{},mean:{},std:{}" , cur.first,
                    c.m_n1,c.m_n2, c.m_z, c.m_zPrev, x,y, c.m_slope, c.m_intercept,c.m_mean, c.m_std);

            if (cur.second > forceCloseTime ) {
                if (c.m_position1.m_position != 0 ) {
                    m_log->warn("next day Close position {}_{} {} {} " , c.m_n1,c.m_n2, x,y);
                    m_profits .push_back( c.closePosition(x,y,ext));
                }
            }
            else {
                if (c.m_position1.m_position == 0 ) {
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
                else { // Position have been hold.
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
                            if (abs(zPrev -z0)> 0.5  ) {
                                m_log->warn("[-{}_+{}] Wow profit close Position z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0);
                                m_profits .push_back( c.closePosition(x,y,ext));
                            }
                        else { //wait for the profit point
                            m_log->debug("[{}_{}] Wait for the profit point z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0); 
                        }
                        }
                        else { //uder loss state
                            if (zdiff > 1.5 && !isProfit) { //cut loss
                                m_log->warn("[-{}_+{}] Stop loss close Position z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0);
                                m_profits .push_back( c.closePosition(x,y,ext));
                            }
                            else { //draw down
                                m_log->debug("[{}_{}] Drawdown. maybe increase position z:{}, zPrev:{} z0 {}" , c.m_n1,c.m_n2, z,zPrev,z0); 
                            }
                        }


                    }

                }
            }
            c.m_zPrev = c.m_z;
    });

}
