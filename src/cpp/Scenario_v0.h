//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once

#include <map>
#include <vector>

#include "contract.h"
#include "strategy.h"
#include "scenario.h"


class Scenario_v0 : public IScenario {
public:
    Scenario_v0(const char * pairCsv, const char * conf = nullptr) ;
    virtual void execute();
    virtual void postSetup();
    virtual ~Scenario_v0() {}
    virtual void debug(LogType *log = nullptr);
    virtual std::vector<SnapData> &  getSymbolList()  { return m_snapDataVector;}
protected:
    void setupContractPairTrades(const char *pairCsv);
private:
    std::vector<ContractPairTrade> m_contracts;
    std::vector<SnapData> m_snapDataVector;

    std::vector<std::pair<SnapData*, ContractPairTrade* >   > m_snapAsN1;
    std::vector<std::pair<SnapData*, ContractPairTrade* >   > m_snapAsN2;
    LogType  m_log;
};
