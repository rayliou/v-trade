#include "twsapi_macunix.1019.02/IBJts/source/cppclient/client/EDecoder.h"
#include "v_subcmds.h"
#include "V_IB_Receiver.h"

// https://interactivebrokers.github.io/tws-api/historical_bars.html

static LogType s_log = spdlog::stderr_color_mt("History");
void v_tws_history(CmdOption &cmd){
    const char * conf = cmd.get("--conf");
    s_log->debug("Loading conf from {}", conf);
    auto * ibSender = g_pIBReceiver->getClient();
    //  IBApi.EClient.reqWshMetaData must be successfully called once per day after server restart, prior to making any calls to IBApi.EClient.reqWshEventData, 
    std::string endDateTime = "20240201 23:59:59 US/Eastern";
    std::string durationStr    = "200 D";
    std::string barSizeSetting  = "1 day";

    Contract contract;
    contract.secType = "STK";
    contract.currency = "USD";
    contract.exchange = "SMART";
    contract.symbol = "AMD";
    contract.conId    = 4391;
    contract.symbol = "JPM";
    contract.conId    = 1520593;

    auto chartOptions = std::make_shared<TagValueList>();
    // void V_IB_Sender::reqHistoricalData(TickerId tickerId, const Contract& contract,
    //                                 const std::string& endDateTime, const std::string& durationStr,
    //                                 const std::string&  barSizeSetting, const std::string& whatToShow,
    //                                 int useRTH, int formatDate, bool keepUpToDate, const TagValueListSPtr& chartOptions) {

    //Schedule: Session. Start: 20231124-09:30:00, End: 20231124-13:00:00, RefDate: 20231124
    ibSender->reqHistoricalData(111, contract, endDateTime, durationStr, barSizeSetting, "SCHEDULE", 1, 1, false, chartOptions);







    std::this_thread::sleep_for(std::chrono::seconds(10));

    return;

}
