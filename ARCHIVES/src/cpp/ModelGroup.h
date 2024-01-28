//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#pragma once
#include "common.h"
#include <execution>
#include "scenario.h"
#include "Scenario_v1.h"

class ModelGroup {
public:
    virtual void run (bool *stopFlag)  = 0;
    ModelGroup(CmdOption &cmd);
    virtual ~ModelGroup();
protected:
    void addScenario(string & modelPath);
    std::vector<IScenario *> m_scenarios;
    CmdOption & m_cmd;
    json m_jsonConf;
    map<string,BigTable *> m_bigtables;
    list<string> m_modelFilePaths;
    //singleton
    SnapDataMap  m_snapDataMap;
private:
    bool * m_stopFlag {nullptr};
    static LogType  m_log;
};
