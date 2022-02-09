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
    virtual void postSetup();

    virtual void runBT();
    virtual ~Scenario_v1() {}
    virtual void debug(LogType *log = nullptr);
private:
    void preRunBT();
    void postRunBT();
    void updateSnapDataByBigTable(int pos, SnapData &snap);
    void updateSnapDataByBigTable(int pos);
    void calContractDiffData(ContractPairTrade &c, DiffData &d);
    void strategy(ContractPairTrade &c) ;
    void rank(std::vector<ContractPairTrade *> &openCtrcts,std::vector<ContractPairTrade *> &closeCtrcts) ;
    void executeTrades(std::vector<ContractPairTrade *> &openCtrcts,std::vector<ContractPairTrade *> &closeCtrcts) ;

    std::list<ContractPairTrade> m_contracts;

    //std::vector<std::pair<SnapData*, ContractPairTrade* >   > m_snapAsN1;
    //std::vector<std::pair<SnapData*, ContractPairTrade* >   > m_snapAsN2;
    std::string m_modelFilePath;
    Money m_money;
    static LogType  m_out;
    BigTable &m_bigtable;
    time_t m_modelTime;
    time_t m_startTime;;
    std::ostream * m_pOutWinDiff {nullptr};
    const char * m_outTraceDataPath  {nullptr};
private:

    //85-, 92
    #if 0
    const int SKIP_1ST_SECS = 16 * 60;
    const float STD_RATE_STOPDIFF = 0.2; //0.4;  //2.5; //1.3; //1.9;
    #endif
    const int SKIP_1ST_SECS = 15 * 60;
    const float STD_RATE_STOPDIFF = 0.5; //0.4;  //2.5; //1.3; //1.9;

    const float THRESHOLD_STD_PERCENT = 0.25;
    // const int MAXBARS_STD_CHECK = 1;

    const float THRESHOLD_Z_L = 1.90;
    const float THRESHOLD_Z_H = 2.1;
};
