//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once

#include <map>
#include <vector>

#include "contract.h"
#include "strategy.h"
#include "scenario.h"

#include "3rd-party/spdlog/include/spdlog/spdlog.h"
#include "3rd-party/spdlog/include/spdlog/sinks/stdout_color_sinks.h"

class Scenario_v0 : public IScenario {
public:
    Scenario_v0(const char * pairCsv, const char * conf = nullptr) ;
    virtual void execute(){
                throw std::runtime_error("needed to be implement" + string(__FUNCTION__));
    }
    virtual ~Scenario_v0() {}
    virtual std::vector<SnapData> &  getSymbolList()  { return m_snapDataVector;}
protected:
    void setupContractPairTrades(const char *pairCsv);
private:
    std::vector<ContractPairTrade> m_contracts;
    std::vector<SnapData> m_snapDataVector;
    LogType  m_log;
};
