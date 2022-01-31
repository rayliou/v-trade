//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once

#include <map>
#include <vector>
#include <list>

#include "contract.h"
#include "strategy.h"
#include "scenario.h"
#include "ContractPairTrade.h"
#include "BigTable.h"

// ~/stock/env_study/2022-01-12.cn/js_coint.json
// {"pair":"BZUN_GDS","s_0":10.19418,"s_dayslr":4.71023,"s_daysfast":3.20328,
// "s_hllr":2.08931,"s_hlfast":3.24254,"std_rate":1.59872,"coint_days":14,
// "interval_secs":60.0,"he_0":0.32497,"hl_bars_0":116.92,
// "start":1640793540000,"end":1642003140000}
//
// 1. a Scenario per slope
// 2. updateData into every ssnapData onece trigering.
// 3. 
class Scenario_v1 : public IScenario {
public:
    Scenario_v1(std::string name, CmdOption &cmd,SnapDataMap & snapDataMap,const char * modelFilePath, BigTable & bigtable);

    virtual void runBT();



    virtual void preOneEpoch(const std::map<std::string, std::any>& ext);
    virtual void postOneEpoch(const std::map<std::string, std::any>& ext);
    virtual void postSetup();
    virtual ~Scenario_v1() {}
    virtual void debug(LogType *log = nullptr);
    virtual std::string getConfPath() const { return m_pairCsv; }
private:
    void updateSnapDataByBigTable(int pos);
    void strategy() ;
    void rank(std::vector<ContractPairTrade *> &contracts ) ;
    void executeTrades(vector<ContractPairTrade *> &contracts) ;

    std::list<ContractPairTrade> m_contracts;

    //std::vector<std::pair<SnapData*, ContractPairTrade* >   > m_snapAsN1;
    //std::vector<std::pair<SnapData*, ContractPairTrade* >   > m_snapAsN2;
    std::string m_pairCsv;
    Money m_money;
    static LogType  m_out;
    BigTable &m_bigtable;
    time_t m_modelTime;
};
