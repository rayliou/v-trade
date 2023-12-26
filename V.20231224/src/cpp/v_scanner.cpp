
#include "v_subcmds.h"
#include "V_IB_Receiver.h"

// https://interactivebrokers.github.io/tws-api/market_scanners.html

static LogType s_log = spdlog::stderr_color_mt("v_scanner");
void v_scanner(CmdOption &cmd){
    const char * conf = cmd.get("--conf");
    s_log->debug("Loading conf from {}", conf);

    bool stopFlag = false;
    VectorOfPtrVContract vcontract_vector;
    V_IB_Receiver ib0(cmd, stopFlag, &vcontract_vector);
    std::jthread thIB(&V_IB_Receiver::run, &ib0);
    ib0.waitConnected();
    V_IB_Receiver* ib = &ib0;
    ib->setJThread(&thIB);
    // ib->setRemainingCnt(symbolsSet.size());
    V_IB_Sender *ibSender = ib->getClient();
    ibSender->reqScannerParameters();
    std::this_thread::sleep_for(std::chrono::seconds(10));
    stopFlag  = true;

    return;


}
