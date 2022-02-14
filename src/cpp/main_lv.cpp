//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include "scenario.h"
//#include "Scenario_v0.h"
#include "Scenario_v1.h"

#include "Backtest.h"

// https://github.com/gabime/spdlog
// https://interactivebrokers.github.io/tws-api/client_wrapper.html#ewrapper_impl



int main(int argc, char * argv[]) {
    CmdOption cmd(argc,argv);
    spdlog::cfg::load_env_levels();
    Backtest bt(cmd);
    bt.run(); return 0;

    spdlog::info("{}", cmd.str());
    return 0;
}
