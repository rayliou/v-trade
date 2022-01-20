//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#include "common.h"

#include "Scenario_v0.h"
#include <fstream>
#include <numeric>

//https://github.com/vincentlaucsb/csv-parser
#include "3rd-party/csv-parser/single_include/csv.hpp"

using namespace std;

Scenario_v0::Scenario_v0(const char * pairCsv, const char * conf)  {
        m_log = spdlog::stdout_color_mt(typeid(*this).name());
    //m_log = spdlog::stdout_color_mt("Scenario_v0");
    setupContractPairTrades(pairCsv);
    for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
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
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto s ) {
            s.debug(m_log);
            if(s.m_isAvailable) {
                s.m_n1SnapData->debug(*log);
                s.m_n2SnapData->debug(*log);
            }
    });
}
void Scenario_v0::setupContractPairTrades(const char *pairCsv) {
    using namespace csv;
    CSVReader reader(pairCsv);
    for (CSVRow& row: reader) {
        m_contracts.push_back(ContractPairTrade(row));
    }
}
void Scenario_v0::postSetup() {
    std::vector<SnapData>::iterator it0;
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto & s ) {
        for(auto it = m_snapDataVector.begin(); it != m_snapDataVector.end(); it++) {
            if (s.m_n1 == it->symbol) {
                s.m_n1SnapData = it;
            }
            if (s.m_n2 == it->symbol) {
                s.m_n2SnapData = it;
            }
            if (s.m_n1SnapData != it0 && s.m_n2SnapData != it0) {
                s.m_isAvailable = true;
            }

        }
    });
}
void Scenario_v0::summary(const std::map<std::string, std::any>& ext) {

    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto & c ) {
        m_log->debug("[{}_{}] Profit:{} " , c.m_n1,c.m_n2, c.m_profit);
    });
    auto &v = m_profits;
    auto sum = std::accumulate(v.begin(), v.end(), 0.0);
    auto mean = sum / v.size();
    auto sq_sum = std::inner_product(v.begin(), v.end(), v.begin(), 0.0);
    auto stdev = std::sqrt(sq_sum / v.size() - mean * mean);
    m_log->debug("Total:{}, mean: {}, std:{},sum:{}", v.size(),mean, stdev, sum);

}
void Scenario_v0::execute(const std::pair<std::string, time_t>  & cur,const std::pair<std::string, time_t>  & start ) {
    m_profits.clear();
    //return;
    auto secsFromStart = cur.second - start.second;
    int daysAfterStart = secsFromStart/(3600 * 24);
    std::map<std::string, std::any>  ext;
    ext["start"] = start;
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto &c ) {
            if (!c.isAvailable()) {
                return;
            }
            auto x = c.m_n1SnapData->close;
            auto y = c.m_n2SnapData->close;
            auto diff = x * c.m_slope + c.m_intercept - y;
            c.m_z = (diff - c.m_mean)/c.m_std;
            if (daysAfterStart >0) {
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
                        c.newPosition(x,y,true, ext);
                    }
                    else if ( c.m_z > 2.0) {
                        m_log->warn("[-{}_+{}] new Position z:{}, zPrev:{} " , c.m_n1,c.m_n2, c.m_z, c.m_zPrev);
                        c.newPosition(x,y,false, ext);
                    }
                    else {
                        m_log->debug("[{}_{}] Do nothing  z:{}, zPrev:{} " , c.m_n1,c.m_n2, c.m_z, c.m_zPrev);
                    }
                }
                else { // Position have been hold.
                    auto z0 = c.m_z0;
                    auto z = c.m_z;
                    auto zPrev = c.m_zPrev;
                    if (((z0 < 0) &&  (z - z0) < -1.0) ||  ((z0 > 0) && (z - z0) > 1.0)) {
                        m_log->warn("[-{}_+{}] Stop loss close Position z:{}, zPrev:{} z0" , c.m_n1,c.m_n2, z,zPrev,z0);
                        m_profits .push_back( c.closePosition(x,y,ext));
                    }
                    else if (((z0 < 0) && (z > zPrev) ) || ((z0 > 0) && (z < zPrev) )) {
                        //trail 
                        m_log->debug("[{}_{}] Trail near z:{}, zPrev:{} " , c.m_n1,c.m_n2, c.m_z, c.m_zPrev);
                    }
                    else if (((z0 < 0) && (z - z0) > 1.0) || ((z0 > 0) && (z - z0) < -1.0)) {
                        //Profit Wow.....
                        m_log->warn("[{}_{}] Profit Wow  Position z:{}, zPrev:{} z0" , c.m_n1,c.m_n2, z,zPrev,z0);
                        m_profits .push_back( c.closePosition(x,y,ext));
                    }
                    else {
                        m_log->debug("[{}_{}] Do nothing  z:{}, zPrev:{} " , c.m_n1,c.m_n2, c.m_z, c.m_zPrev);
                    }

                }
            }
            c.m_zPrev = c.m_z;
            // c.m_n1SnapData->debug(m_log);
            // c.m_n2SnapData->debug(m_log);
    });

}
