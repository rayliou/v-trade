//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include "scenario.h"
#include "Backtest.h"

LogType Backtest::m_log = spdlog::stderr_color_mt("Backtest");
Backtest::Backtest(CmdOption &cmd):m_cmd(cmd) {
    string btJPath = "./bt.json";
    std::ifstream is(btJPath);
    is >> m_jsonConf;
    for (auto& [k, v] :m_jsonConf["big_table"].items()) {
        string path;
        v.get_to(path);
        BigTable * b  = new BigTable(path.c_str());
        m_bigtables[k] = b;
        m_log->debug("Loaded bigtable: {}->{}", k, path);
        b->debug(m_log);
    }
    const char * modelPath = m_cmd.get("--model");
    if ( nullptr != modelPath) {
        string path(modelPath);
        addScenario(path);
    }
    else {
        std::ifstream is("./ABC.dat");
        for(string line; std::getline(is,line);) {
            addScenario(line);
        }
    }

}
Backtest::~Backtest() {
    for (auto& [k, v] :m_bigtables) {
        delete v;
        m_log->debug("Unloaded bigtable: {}", k);
    }
    m_bigtables.clear();
    for(auto  s: m_scenarios) {
        m_log->debug("delete scenario: {}", s->getName());
        delete s;
    }
}
void Backtest::addScenario(string & modelPath) {
    m_modelFilePaths.push_back(modelPath);
    auto [group,date] = Scenario_v1::getGroupDateFromPath(modelPath);
    string name = "v1-";
    name += group;
    name += "-";
    name += date;
    auto it = m_bigtables.find(group);
    if(m_bigtables.end() == it) {
        throw std::runtime_error("Cannot find " + group + "in m_bigtables");
    }
    BigTable * pTable = it->second;

    Scenario_v1 *s = new Scenario_v1(name, m_cmd, m_snapDataMap,modelPath.c_str(), *pTable);
    // s->postSetup();
    m_scenarios.push_back(s);
    m_log->debug("Loaded  Scenario: {}\t{}",s->getName(),modelPath);
}
void Backtest::run() {
    // string groups [] {"cn", "topV100_MC200"};
    for_each(m_scenarios.begin(),m_scenarios.end(),[&](IScenario * i){
        i->setMoney(nullptr);
        i->runBT();
        json &&j = i->getJResult();
        m_log->warn("{}", j.dump());
    }); 

}
