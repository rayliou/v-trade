//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#pragma once
#include "common.h"
#include <execution>
// #include "BigTable.h"
// #include "scenario.h"
// #include "Scenario_v1.h"


// https://interactivebrokers.github.io/tws-api/client_wrapper.html#The
class IBTWS {
public:
    IBTWS(CmdOption &cmd);
    virtual ~IBTWS();
    void run() ;
    void addScenario(string & modelPath);

private:
    CmdOption & m_cmd;
    json m_jsonConf;
    static LogType  m_log;

    // std::vector<IScenario *> m_scenarios;
    // map<string,BigTable *> m_bigtables;
    // list<string> m_modelFilePaths;
    // //singleton
    // SnapDataMap  m_snapDataMap;
};
