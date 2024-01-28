#include "twsapi_macunix.1019.02/IBJts/source/cppclient/client/EDecoder.h"
#include "v_subcmds.h"
#include "V_IB_Receiver.h"

// https://interactivebrokers.github.io/tws-api/wshe_filters.html

static LogType s_log = spdlog::stderr_color_mt("Events");
void v_tws_events(CmdOption &cmd){
    const char * conf = cmd.get("--conf");
    s_log->debug("Loading conf from {}", conf);
    auto * ibSender = g_pIBReceiver->getClient();
    //  IBApi.EClient.reqWshMetaData must be successfully called once per day after server restart, prior to making any calls to IBApi.EClient.reqWshEventData, 
    ibSender->cancelWshMetaData(110);
    ibSender->reqWshMetaData(110);
    s_log->debug("reqWshMetaData(110)");
    std::this_thread::sleep_for(std::chrono::seconds(3));

    std::this_thread::sleep_for(std::chrono::seconds(10));
	//WshEventData(int conId, bool fillWatchlist, bool fillPortfolio, bool fillCompetitors, std::string startDate, std::string endDate, int totalLimit)
    WshEventData wshEventData(4391 //AMD
        ,false,false,false
        ,"20130101", ""
        ,1000
    );
    ibSender->cancelWshEventData(111);
    ibSender->reqWshEventData(111,wshEventData);
    s_log->debug("ibSender->reqWshEventData(111,wshEventData)");








    std::this_thread::sleep_for(std::chrono::seconds(10));

    return;

}
