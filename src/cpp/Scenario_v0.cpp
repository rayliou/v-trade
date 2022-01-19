//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#include "common.h"

#include "Scenario_v0.h"

using namespace std;

Scenario_v0::Scenario_v0(const char * conf) :m_log (spdlog::stdout_color_mt("Scenario_v0")) {
    m_log = spdlog::stdout_color_mt("Scenario_v0");
    for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
        auto symbols = c.getSymbols();
        for_each(symbols.begin(), symbols.end(), [&] (ContractPairTrade & symbol ) {
                m_snapDataVector.push_back(SnapData(symbol) )
        });

    });
    for_each(m_snapDataVector.begin(),m_snapDataVector.edn(),[] (auto s ) {
            s.debug(m_log);
    });
}
