//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#include "common.h"

#include "Scenario_v0.h"
#include <fstream>

//https://github.com/vincentlaucsb/csv-parser
#include "3rd-party/csv-parser/single_include/csv.hpp"

using namespace std;

Scenario_v0::Scenario_v0(const char * pairCsv, const char * conf) :m_log (spdlog::stdout_color_mt("Scenario_v0")) {
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
void Scenario_v0::execute() {
    return;
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto s ) {
            s.m_n1SnapData->debug(m_log);
            s.m_n2SnapData->debug(m_log);
    });
}
#if 0
int main(int argc, char * argv[]) {
    spdlog::set_level(spdlog::level::debug);
    Scenario_v0 s("/Users/henry/stock/env_study/2021-12-17.topV100_MC200/ols.csv");
    return 0;
}
#endif
