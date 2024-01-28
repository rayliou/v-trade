#include "VContract.h"
#include "common.h"
#include "CmdOption.h"
#include <memory>
#include <set>
#include <map>
#include <spdlog/spdlog.h>
#include <thread>


#include "v_subcmds.h"


V_IB_Receiver *g_pIBReceiver {nullptr};
std::jthread g_jthread_IB_Receiver;
LogType g_log = spdlog::stderr_color_mt("v-main");
bool g_stopFlag = false;

#define ARG_NOT_NULL(arg) if(nullptr == arg) { throw std::runtime_error("argv --"  #arg " is needed."); }

// https://github.com/gabime/spdlog
// https://interactivebrokers.github.io/tws-api/client_wrapper.html#ewrapper_impl

typedef void (*SubCmdFuncPtr) (CmdOption &cmd) ;
void test_log(CmdOption &cmd){
    g_log->warn("Do nothing {}", __PRETTY_FUNCTION__);

}
static std::map<std::string,SubCmdFuncPtr> mapSubCmds;
void regSubCmd() {
#define CMD_REG(c) mapSubCmds[#c] =c
    // CMD_REG(history_daily_deps);
    // CMD_REG(history);
    // CMD_REG(bt);
    CMD_REG(v_tws_history);
    CMD_REG(v_tws_events);
    CMD_REG(v_news);
    CMD_REG(v_scanner);
    CMD_REG(test_log);
#undef CMD_REG

}
static void preLoadSymbols(CmdOption &cmd,std::set<std::string> &symbolsSet){
// --preload_symbols  topV100_MC200
    const char * preload_symbols  = cmd.get("--preload_symbols");
    if (nullptr == preload_symbols){
        return;
    }
    const char * conf = cmd.get("--conf");
    ARG_NOT_NULL(conf);
    g_log->debug("Loading {} from {}", preload_symbols, conf);
    std::ifstream is(conf);
    json  m_jsonConf;
    is >> m_jsonConf;
    std::string symbols;
    m_jsonConf[preload_symbols].get_to(symbols);
    auto sList = utility::strSplit(symbols, ',', true);
    symbolsSet.insert(sList.begin(), sList.end());
    // for (auto& [k, v] :m_jsonConf["stoks.us.groups"].items()) {
    //     v.get_to(symbols);
    //     auto sList = utility::strSplit(symbols, ',', true);
    //     symbolsSet.insert(sList.begin(), sList.end());
    // }
}
static void initilizePreLoadContracts(CmdOption &cmd, std::set<std::string> &symbolsSet){
    if (symbolsSet.size() == 0) {
        return;
    }
    auto * pVect = g_pIBReceiver->getVContractVector();
    int reqId = 0;
    auto * ibClient = g_pIBReceiver->getClient();
    for(auto &s: symbolsSet ){
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
        pVect->push_back(std::make_unique<VContract>(s.c_str()));
        g_log->trace("reqContractDetails({},{})", reqId, s);
        ibClient->reqContractDetails(reqId++, contract);
        //callback void V_IB_Receiver::contractDetails( int reqId, const ContractDetails& contractDetails) {
    }
    int remain  = 0;
    while((remain = g_pIBReceiver->getRemainingCnt()) > 0 ){
        std::this_thread::sleep_for(std::chrono::seconds(1));
        g_log->debug("Remaining cnt {}", remain);

    }
    for(auto &p : *pVect){
        if (p->ibContractDetails_ == nullptr){ continue; }
        auto & c = p->ibContractDetails_->contract;
        g_log->info("Contract:{}:{}", c.symbol,c.conId);
    }
    return;

}
static void initilizeIBConnection(CmdOption &cmd){
    std::set<std::string> symbolsSet;
    preLoadSymbols(cmd,symbolsSet);
    VectorOfPtrVContract *pVcontract_vector = new VectorOfPtrVContract();
    g_pIBReceiver  = new V_IB_Receiver(cmd, g_stopFlag, pVcontract_vector);
    // 当引用类的成员函数作为参数时（例如，在多线程或回调场景中），你需要提供该成员函数的指针。这是通过类名、:: 以及成员函数名前加上 & 符号来实现的。
    g_jthread_IB_Receiver = std::jthread (&V_IB_Receiver::run, g_pIBReceiver);
    g_pIBReceiver->waitConnected();
    g_pIBReceiver->setJThread(&g_jthread_IB_Receiver);
    V_IB_Sender *ibClient = g_pIBReceiver->getClient();
    g_pIBReceiver->setRemainingCnt(symbolsSet.size());
    // std::vector<SnapData *> m_ibSnapDataVct;
    initilizePreLoadContracts(cmd, symbolsSet);
    g_log->debug("End {}", __FUNCTION__);
}
static void terminateIBConnection(CmdOption &cmd){
    g_stopFlag  = true;
    while(g_pIBReceiver->isConnected()) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    delete  g_pIBReceiver;
    g_pIBReceiver = nullptr;
    g_log->warn("End {}", __FUNCTION__);
}


int main(int argc, char * argv[]) {
    // test(); return 0;
    //  SPDLOG_LEVEL=trace,v-main=trace
    spdlog::cfg::load_env_levels();
    if ( argc == 1) {
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
// --preload_symbols  topV100_MC200

    initilizeIBConnection(cmd);
    it->second(cmd);
    terminateIBConnection(cmd);
    return 0;
}

#include <clickhouse/client.h>
int test() {
    using namespace clickhouse;
     /// Initialize client connection.
    Client client(ClientOptions().SetHost("localhost"));

    /// Create a table.
    client.Execute("CREATE TABLE IF NOT EXISTS default.numbers (id UInt64, name String) ENGINE = Memory");

    /// Insert some values.
    {
        Block block;

        auto id = std::make_shared<ColumnUInt64>();
        id->Append(1);
        id->Append(7);

        auto name = std::make_shared<ColumnString>();
        name->Append("one");
        name->Append("seven");

        block.AppendColumn("id"  , id);
        block.AppendColumn("name", name);

        client.Insert("default.numbers", block);
    }

    /// Select values inserted in the previous step.
    client.Select("SELECT id, name FROM default.numbers", [] (const Block& block)
        {
            for (size_t i = 0; i < block.GetRowCount(); ++i) {
                std::cout << block[0]->As<ColumnUInt64>()->At(i) << " "
                          << block[1]->As<ColumnString>()->At(i) << "\n";
            }
        }
    );

    /// Delete table.
    //client.Execute("DROP TABLE default.numbers");

    return 0;
}