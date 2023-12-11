#include "common.h"
#include "CmdOption.h"
#include <set>
#include <map>
#include <spdlog/spdlog.h>

#include "V_IB_EClientSocket.h"
#include "V_IB_EWrapper.h"

// FYI: src/cpp/main_lv.cpp


LogType g_log = spdlog::stderr_color_mt("v-main");
#define ARG_NOT_NULL(arg) if(nullptr == arg) { throw std::runtime_error("argv --"  #arg " is needed."); }

// https://github.com/gabime/spdlog
// https://interactivebrokers.github.io/tws-api/client_wrapper.html#ewrapper_impl

typedef void (*SubCmdFuncPtr) (CmdOption &cmd) ;
void test_log(CmdOption &cmd){
    const char * conf = cmd.get("--conf");
    ARG_NOT_NULL(conf);
    g_log->debug("Loading conf from {}", conf);
    std::ifstream is(conf);
    json  m_jsonConf;
    is >> m_jsonConf;
    //Get symbol list
    std::set<std::string> symbolsSet;
    for (auto& [k, v] :m_jsonConf["stoks.us.groups"].items()) {
        std::string symbols;
        v.get_to(symbols);
        auto sList = utility::strSplit(symbols, ',', true);
        symbolsSet.insert(sList.begin(), sList.end());
    }
    //
    // for(auto & v:symbolsSet){ g_log->debug("{}",v); }
    bool stopFlag = false;
    V_IB_EWrapper ib0(cmd, stopFlag);
    std::jthread thIB(&V_IB_EWrapper::run, &ib0);
    ib0.waitConnected();
    V_IB_EWrapper* ib = &ib0;
    ib->setJThread(&thIB);
    //g_log->trace("sleep 5s");
    //std::this_thread::sleep_for(std::chrono::seconds(5));
    //g_log->trace("after sleep 5s");
    V_IB_EClientSocket *ibClient = ib->getClient();
    // std::vector<SnapData *> m_ibSnapDataVct;
    // m_ibSnapDataVct.clear();
    // g_log->trace("call setSnapDataVct ");
    // ib->setSnapDataVct(&m_ibSnapDataVct);
    // ib->resetSnapUpdateCnt();


    int reqId = 0;
    for(auto &s: symbolsSet){
        Contract contract;
        contract.symbol = s;
        contract.secType = "STK";
        contract.currency = "USD";
        contract.exchange = "SMART";
        if( s == "LLY" ) {
            contract.primaryExchange = "NYSE";
        }
        if(s == "CD" ) {
            contract.primaryExchange = "NASDAQ";
        }
        // auto v = new SnapData(s);
        // v->ibUpdated = false;
        // m_ibSnapDataVct.push_back(v);
        g_log->trace("reqContractDetails({},{})", reqId, s);
        ibClient->reqContractDetails(reqId++, contract);
    }
    std::this_thread::sleep_for(std::chrono::seconds(30));
#if 0
    int doneCnt ;
    auto total = symbolsSet.size();
    bool ret =  ( (doneCnt = ib->getSnapUpdateCnt()) < total);
    g_log->trace("( (doneCnt {}  = ib->getSnapUpdateCnt() {}  ) < total {} ) ={} ;", doneCnt,ib->getSnapUpdateCnt() ,total, ret);

    while ( (doneCnt = ib->getSnapUpdateCnt()) < total) {
        g_log->trace("wait:{}/{}:reqContractDetails",doneCnt, total );
        std::this_thread::sleep_for(std::chrono::seconds(1));
        bool ret =  ( (doneCnt = ib->getSnapUpdateCnt()) < total);
        g_log->trace("( (doneCnt {}  = ib->getSnapUpdateCnt() {}  ) < total {} ) ={} ;", doneCnt,ib->getSnapUpdateCnt() ,total, ret);
    }
    ret =  ( (doneCnt = ib->getSnapUpdateCnt()) < total);
    g_log->trace("AFTER ( (doneCnt {}  = ib->getSnapUpdateCnt() {}  ) < total {} ) ={} ;", doneCnt,ib->getSnapUpdateCnt() ,total, ret);
#endif

}
static std::map<std::string,SubCmdFuncPtr> mapSubCmds;
void regSubCmd() {
#define CMD_REG(c) mapSubCmds[#c] =c
    // CMD_REG(history_daily_deps);
    // CMD_REG(history);
    // CMD_REG(bt);
    CMD_REG(test_log);
#undef CMD_REG

}


int main(int argc, char * argv[]) {
    spdlog::cfg::load_env_levels();
    if ( argc == 1) {
        // throw std::runtime_error("argv[1] MUST be set!");
        spdlog::critical("argv[1] MUST be set!"); exit(-1);
    }
    CmdOption cmd(argc,argv);
    regSubCmd();
    auto it = mapSubCmds.find(argv[1]);
    if (it == mapSubCmds.end()) {
        std::ostringstream os;
        for(auto &[k,v]:mapSubCmds) {
            os << k << ",";
        }
        spdlog::critical("argv[1] MUST be one of [{}]", os.str()); 
        exit(-1);
    }
    it->second(cmd);
    return 0;
}
