//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include "scenario.h"
#include "ModelGroup.h"

LogType ModelGroup::m_log = spdlog::stderr_color_mt("ModelGroup");
ModelGroup::ModelGroup(CmdOption &cmd) :m_cmd(cmd){
    const char * conf = m_cmd.get("--conf");
    const char * modelPath = m_cmd.get("--model");
    if(nullptr == conf) {
        throw std::runtime_error("argv -conf is needed.");
    }
    m_log->debug("Loading conf from {}", conf);
    std::ifstream is(conf);
    is >> m_jsonConf;
    for (auto& [k, v] :m_jsonConf["big_table"].items()) {
        string path;
        v.get_to(path);
        BigTable * b  = new BigTable(path.c_str());
        m_bigtables[k] = b;
        m_log->debug("Loaded bigtable: {}->{}", k, path);
        b->debug(m_log);
    }
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
ModelGroup::~ModelGroup() {
    for (auto& [k, v] :m_bigtables) {
        delete v;
        m_log->debug("Unloaded bigtable: {}", k);
    }
    m_bigtables.clear();
    for(IScenario * s: m_scenarios) {
        string name = s->getName();
        m_log->debug("delete scenario: {}", name);
        delete s;
    }
}
void ModelGroup::addScenario(string & modelPath) {
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
