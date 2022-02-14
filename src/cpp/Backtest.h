//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#pragma once
#include "common.h"
#include <execution>
#include "scenario.h"
#include "Scenario_v1.h"


class Backtest {
public:
    Backtest(CmdOption &cmd);
    virtual ~Backtest();
    void run() ;
    void addScenario(string & modelPath);

private:
    std::vector<IScenario *> m_scenarios;
    CmdOption & m_cmd;
    json m_jsonConf;
    map<string,BigTable *> m_bigtables;
    list<string> m_modelFilePaths;
    //singleton
    SnapDataMap  m_snapDataMap;
    static LogType  m_log;
};
