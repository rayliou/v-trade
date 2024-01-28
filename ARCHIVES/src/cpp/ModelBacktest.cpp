//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include "scenario.h"
#include "ModelBacktest.h"

LogType ModelBacktest::m_log = spdlog::stderr_color_mt("ModelBacktest");
ModelBacktest::ModelBacktest(CmdOption &cmd):ModelGroup(cmd) {

}
ModelBacktest::~ModelBacktest() {
}
void ModelBacktest::run(bool *stopFlag) {
    // string groups [] {"cn", "topV100_MC200"};
    for_each(m_scenarios.begin(),m_scenarios.end(),[&](IScenario * i){
        i->setMoney(nullptr);
        i->runBT();
        json &&j = i->getJResult();
        m_log->warn("{}", j.dump());
    }); 

}
