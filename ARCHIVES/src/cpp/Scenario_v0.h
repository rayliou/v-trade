//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once

#include <map>
#include <vector>
#include <list>

#include "strategy.h"
#include "scenario.h"
#include "ContractPairTrade.h"


class Scenario_v0 : public IScenario {
public:
    Scenario_v0(const char * pairCsv, CmdOption &cmd, const char * conf= nullptr) ;
    virtual void runOneEpoch(const std::pair<std::string, time_t>  & cur,const std::pair<std::string, time_t>  & start );
    virtual void preOneEpoch(const std::map<std::string, std::any>& ext);
    virtual void postOneEpoch(const std::map<std::string, std::any>& ext);
    virtual void postSetup();
    virtual ~Scenario_v0() {}
    virtual void debug(LogType *log = nullptr);
    virtual std::vector<SnapData> &  getSnapDataList()  { return m_snapDataVector;}
    virtual std::string getConfPath() const { return m_pairCsv; }
protected:
    void setupContractPairTrades(const char *pairCsv);
private:
    std::list<ContractPairTrade> m_contracts;
    std::vector<SnapData> m_snapDataVector;

    //std::vector<std::pair<SnapData*, ContractPairTrade* >   > m_snapAsN1;
    //std::vector<std::pair<SnapData*, ContractPairTrade* >   > m_snapAsN2;
    std::string m_pairCsv;
    Money m_money;
    static LogType  m_log;
    static LogType  m_out;
};
