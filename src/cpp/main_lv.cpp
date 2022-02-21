//g++ -g  -std=c++20  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include <set>
#include <filesystem>
#include <thread>

#include "ModelLive.h"
#include "IBTWSApp.h"
#include "IBTWSClient.h"

namespace fs=std::filesystem;

// https://github.com/gabime/spdlog
// https://interactivebrokers.github.io/tws-api/client_wrapper.html#ewrapper_impl
LogType g_log = spdlog::stderr_color_mt("main_lv");
typedef void (*SubCmdFuncPtr) (CmdOption &cmd) ;
#define ARG_NOT_NULL(arg) if(nullptr == arg) { throw std::runtime_error("argv --"  #arg " is needed."); }


void history(CmdOption &cmd) {
	// $(RUN_DIR)/main_lv history -o $@ --dt $* --barSizeSetting "5 secs" --whatToShow "TRADES,BID_ASK" --useRTH 1 --formatDate 1 --sym_source model [--timeout 1800]
    // $(RUN_DIR)/main_lv history -o $@ --dt $* --barSizeSetting "5 secs" --whatToShow "TRADES,BID_ASK" --useRTH 1 --formatDate 1 --sym_source model [--timeout 1800]
    const char * out_dir = cmd.get("--out_dir");
    ARG_NOT_NULL(out_dir);
    auto dt_to    = cmd.get("--dt_to");
    auto dt_from  = cmd.get("--dt_from");
    ARG_NOT_NULL(dt_to);
    ARG_NOT_NULL(dt_from);


    const char * barSizeSetting = cmd.get("--barSizeSetting");
    ARG_NOT_NULL(barSizeSetting);

    const char * whatToShow = cmd.get("--whatToShow");
    whatToShow = (nullptr == whatToShow)?"TRADES":whatToShow;
    const char * useRTH = cmd.get("--useRTH");
    int nUseRTH = (nullptr == useRTH )? 1: atoi(useRTH);
    const char * formatDate = cmd.get("--formatDate");
    int nFormatDate = (nullptr ==formatDate )? 1: atoi(formatDate );
    //
    auto symSource    = cmd.get("--sym_source");
    if(nullptr == symSource) {
        throw std::runtime_error("--sym_source MUST be set!");
    }
    if (0 == strcmp("conf",symSource)) {

        const char * conf = cmd.get("--conf");
        ARG_NOT_NULL(conf);
        g_log->debug("Loading conf from {}", conf);
        std::ifstream is(conf);
        json  m_jsonConf;
        is >> m_jsonConf;
        set<string> symbolsSet;
        for (auto& [k, v] :m_jsonConf["stoks.us.groups"].items()) {
            string symbols;
            v.get_to(symbols);
            auto sList = utility::strSplit(symbols, ',', true);
            symbolsSet.insert(sList.begin(), sList.end());
        }
        bool stopFlag = false;

        IBTWSApp ib0(cmd, stopFlag);
        std::jthread thIB(&IBTWSApp::run, &ib0);
        ib0.waitConnected();
        IBTWSApp* ib = &ib0;
        ib->setJThread(&thIB);
        //g_log->trace("sleep 5s");
        //std::this_thread::sleep_for(std::chrono::seconds(5));
        //g_log->trace("after sleep 5s");
        IBTWSClient *ibClient = ib->getClient();
        std::vector<SnapData *> m_ibSnapDataVct;
        m_ibSnapDataVct.clear();
        g_log->trace("call setSnapDataVct ");
        ib->setSnapDataVct(&m_ibSnapDataVct);
        ib->resetSnapUpdateCnt();


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
            auto v = new SnapData(s);
            v->ibUpdated = false;
            m_ibSnapDataVct.push_back(v);
            //g_log->trace("reqContractDetails({},{})", reqId, s);
            ibClient->reqContractDetails(reqId++, contract);
        }
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
        //for(auto v:m_ibSnapDataVct) {
            //v->debug(g_log);
            //delete v;
        //}
        Ohlcv::TimeMapOhlcv timeMapOhlcv;
        Ohlcv::ValuesOhlcv valuesOhlcv(total);
        reqId = 0;
        for(SnapData * s: m_ibSnapDataVct){
            auto c = s->ibContractDetails->contract;
            valuesOhlcv[reqId++] = Ohlcv(c.symbol);
        }
        ib->setReceiver(&valuesOhlcv, &timeMapOhlcv);

        string startTime(dt_from);

        string endPrefix(64,'\0');
        struct tm t;
        memset(&t,0, sizeof(t));
        strptime(dt_to, "%Y%m%d", &t);
        strftime(endPrefix.data(), endPrefix.size(),"%Y%m%d",&t);
        endPrefix.resize(strlen(endPrefix.data()));

        string endTime(endPrefix);

        startTime += "  09:30:00";
        endTime   += "  16:00:00";
        fs::path parent(out_dir);
        fs::create_directories(parent);
        map<string,const char *> mapDurationStr {
            {"1 secs", "360 S"},
            {"5 secs", "1800 S"},
            {"30 secs", "10800 S"},
            {"1 min", "1 D"},
        };
        const char * durationStr = mapDurationStr[barSizeSetting];
        g_log->info("Before get data, save dir: {}; Start:{} -> End:{}", parent.c_str(), startTime, endTime);
        do {
            fs::path outPath (parent/(endTime + ".csv"));
            if(fs::exists(outPath)) {
                //get next endTime.
                ifstream is(outPath);
                string line;
                std::getline(is,line);
                std::getline(is,line);
                auto end = line.find(',');
                endTime = line.substr(0,end);
                g_log->info("File {} existed. next endTime:{}", outPath.c_str(),endTime);
            }
            else {
                timeMapOhlcv.clear();
                ib->resetSnapUpdateCnt();
                reqId = 0;
                for(SnapData * s: m_ibSnapDataVct){
                    auto &c = s->ibContractDetails->contract;
                    // https://interactivebrokers.github.io/tws-api/classIBApi_1_1EClient.html#aad87a15294377608e59aec1d87420594
                    //ibClient->reqHistoricalData(reqId++, c, "", "200 S", "5 secs", "MIDPOINT", 0, 2/*1 :string, 2: seconds,  */ ,/*keepUpToDate = */ false,TagValueListSPtr()); 
                    g_log->debug("reqHistoricalData([{}/{}],{},'{}','{}','{}',{},{},{})"
                            ,reqId,total, c.symbol, endTime, durationStr, barSizeSetting, whatToShow, nUseRTH, nFormatDate);
                    ibClient->reqHistoricalData(reqId++, c, endTime, durationStr, barSizeSetting, whatToShow, nUseRTH, nFormatDate/*1 :string, 2: seconds,  */ ,/*keepUpToDate = */ false,TagValueListSPtr()); 
                }
                while ( (doneCnt = ib->getSnapUpdateCnt()) < total) {
                    g_log->trace("wait:{}/{}:reqHistoricalData",doneCnt, total );
                    std::this_thread::sleep_for(std::chrono::seconds(1));
                }
                g_log->trace("timeMapOhlcv.empty:{}", timeMapOhlcv.empty());
                bool ret = (endTime = timeMapOhlcv.begin()->first) > startTime;
                g_log->trace("{} = (endTime:{} = timeMapOhlcv.begin() ->first:{}    ) > startTime {} ",ret,  endTime,timeMapOhlcv.begin()->first,startTime);

                ofstream of(outPath);
                if(!of.is_open()){
                    string msg("Cannot open file: ");
                    throw std::runtime_error(msg +outPath.c_str());
                }
                Ohlcv::dump(timeMapOhlcv, of);
                of.close();
                endTime = timeMapOhlcv.begin()->first;
                g_log->info("Wrote file {} next endTime:{} ", outPath.c_str(), endTime);
            }

        } while  ( endTime > startTime);

        for(auto v:m_ibSnapDataVct) {
            delete v;
        }

        spdlog::info("Stop !!!");
        stopFlag = true;
        //delete ib ;
        //spdlog::info("Stop !!!");
        //thIB.join();
    }
    else if (0 == strcmp("model",symSource)) {
        bool stopFlag = false;
        IBTWSApp ib(cmd, stopFlag);
        std::jthread thIB(&IBTWSApp::run, &ib);
        spdlog::info("{}", cmd.str());
        //get model
        ModelLive mlv(cmd, &ib);
        mlv.history(&stopFlag);
        const char * strTimeout = cmd.get("--timeout");
        auto timeout = (nullptr == strTimeout )?1800:atoi(strTimeout);
        g_log->info("Timeout {}", timeout);
        std::this_thread::sleep_for(std::chrono::seconds(timeout));
        stopFlag = true;
        spdlog::info("Stop !!!");
        thIB.join();
    }
    else {
        throw std::runtime_error("--sym_source unknown!");
    }
}
void history_daily_deps(CmdOption &cmd) {
    // ./b/main_lv history_daily_deps  --dt_to 20220125 --dt_from xxxxx   --port 4096

    const char * output = cmd.get("--output");
    ARG_NOT_NULL(output);
    auto dt_to    = cmd.get("--dt_to");
    if(nullptr == dt_to) {
        throw std::runtime_error("--dt_to MUST be set! --dt_from may be set");
    }
    int days = 60;
    struct tm tmTo;
    memset(&tmTo,0, sizeof(tmTo));
    time_t to,from;
    strptime(dt_to, "%Y%m%d", &tmTo);
    to = mktime(&tmTo);
    auto dt_from  = cmd.get("--dt_from");
    if(nullptr != dt_from) {
        struct tm tmFrom;
        memset(&tmFrom,0, sizeof(tmFrom));
        strptime(dt_from, "%Y%m%d", &tmFrom);
        from = mktime(&tmFrom);
        days = (to -from)/(3600 *24);
    }
    char buf[64];
    strftime(buf, sizeof(buf),"%Y%m%d 16:00:00",&tmTo);
    string endTime(buf);
    string strDays = "";
    ostringstream os;
    os << days << " D";
    strDays = os.str();
    g_log->info("end date:{}, days:{}", endTime, strDays);


    bool stopFlag = false;
    IBTWSApp ib(cmd, stopFlag);
    std::jthread thIB(&IBTWSApp::run, &ib);
    std::this_thread::sleep_for(std::chrono::seconds(3));
    #if 0
    while(!ib.isConnected()) {
        g_log->trace("Wait for connecting.....");
        std::this_thread::sleep_for(std::chrono::microseconds(100));
    }
    #endif
    IBTWSClient *ibClient = ib.getClient();

    Contract contract;
    contract.symbol = "SPY";
    contract.secType = "STK";
    contract.currency = "USD";
    contract.exchange = "SMART";
    bool done = false;
    auto cb1  = [&] ( int reqId, const ContractDetails& contractDetails) -> bool {
        contract = contractDetails.contract;
        done = true;
        //stop
        g_log->trace("cb1: {}", contract.symbol);
        return true;
    };
    ib.setCallback(cb1);
    ibClient->reqContractDetails(0, contract);
    while(!done) {
        g_log->trace("Wait for reqContractDetails");
        std::this_thread::sleep_for(std::chrono::microseconds(50));
    }
    long conId = contract.conId;
    string sym = contract.symbol;
    g_log->debug("contractDetails: {},{}", sym, conId);

    // get history
    done = false;
    list<string> dtList;
    auto cb2  = [&] (TickerId reqId, const Bar& bar) -> bool {
        dtList.push_back(bar.time);
        //s->open = bar.open;
        //s->close = bar.close;
        //s->high = bar.high;
        //s->low  = bar.low;
        //s->volume = bar.volume;
        //s->tm = atol(bar.time.c_str());
        //stop
        //g_log->trace("tm:{},o:{},c:{},h:{},l:{},v:{}", bar.time,bar.open,bar.close,bar.high,bar.low,bar.volume);
        return true;
    };
    auto cbEnd  = [&] (int reqId, const std::string& startDateStr, const std::string& endDateStr) -> bool {
        done = true;
        //stop
        //g_log->trace("Call:{} start:{}, end:{}", __PRETTY_FUNCTION__, startDateStr, endDateStr );
        return true;
    };
    ib.setCallback(cb2);
    ib.setCallback(cbEnd);
    // https://interactivebrokers.github.io/tws-api/historical_limitations.html#hd_step_sizes
    ibClient->reqHistoricalData(1, contract, endTime, strDays, "1 day", "MIDPOINT", 0, 1/*1 :string, 2: seconds,  */ ,/*keepUpToDate = */ false,TagValueListSPtr()); 
    while(!done) {
        std::this_thread::sleep_for(std::chrono::microseconds(50));
    }
    dtList.sort();
    string sP("");
    ofstream of(output);
    for(auto s: dtList) {
        if (nullptr != dt_from && s < dt_from) {
            continue;
        }
        s += ".5s.csv";
        if(!sP.empty()) {
            of << s << ":" << sP << endl;
        }
        sP = s;
    }
    stopFlag = true;
    //spdlog::info("Stop !!!");
    //thIB.join();
}

void live(CmdOption &cmd) {
    bool stopFlag = false;
    IBTWSApp ib(cmd, stopFlag);
    std::jthread thIB(&IBTWSApp::run, &ib);
    spdlog::info("{}", cmd.str());
    //get model
    ModelLive mlv(cmd, &ib);
    mlv.run(&stopFlag);
    std::this_thread::sleep_for(std::chrono::seconds(3));
    stopFlag = true;
    spdlog::info("Stop !!!");
    thIB.join();
}


static map<string,SubCmdFuncPtr> mapSubCmds;
void regSubCmd() {
#define CMD_REG(c) mapSubCmds[#c] =c
    CMD_REG(history_daily_deps);
    CMD_REG(history);
    CMD_REG(live);
#undef CMD_REG

}

int main(int argc, char * argv[]) {
    spdlog::cfg::load_env_levels();
    if ( argc == 1) {
        throw std::runtime_error("argv[1] MUST be set!");
    }
    CmdOption cmd(argc,argv);
    regSubCmd();
    auto it = mapSubCmds.find(argv[1]);
    if (it == mapSubCmds.end()) {
        ostringstream os;
        for(auto &[k,v]:mapSubCmds) {
            os << k << ",";
        }
        throw std::runtime_error("argv[1] MUST be one of [" + os.str() + "]");
    }
    it->second(cmd);
    return 0;
}
