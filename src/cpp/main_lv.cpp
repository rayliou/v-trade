//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include <thread>
#include "scenario.h"
//#include "Scenario_v0.h"
#include "Scenario_v1.h"

#include "Backtest.h"
#include "IBTWSApp.h"

// https://github.com/gabime/spdlog
// https://interactivebrokers.github.io/tws-api/client_wrapper.html#ewrapper_impl



int main(int argc, char * argv[]) {
    CmdOption cmd(argc,argv);
    spdlog::cfg::load_env_levels();
    bool stopFlag = false;
    IBTWSApp ib(cmd, stopFlag);
    std::jthread thIB(&IBTWSApp::run, &ib);
    spdlog::info("{}", cmd.str());
    std::this_thread::sleep_for(std::chrono::seconds(3));
    stopFlag = true;
    spdlog::info("Stop !!!");
    thIB.join();

    return 0;
}
