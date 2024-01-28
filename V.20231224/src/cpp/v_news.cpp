#include "v_subcmds.h"
#include "V_IB_Receiver.h"

// https://interactivebrokers.github.io/tws-api/news.html#news_providers

static LogType s_log = spdlog::stderr_color_mt("vNews");
void v_news(CmdOption &cmd){

    auto list  = std::make_shared<TagValueList>();
    // list->push_back(std::make_shared<TagValue>("manual", "1"));

    const char * conf = cmd.get("--conf");
    s_log->debug("Loading conf from {}", conf);
    auto * ibSender = g_pIBReceiver->getClient();

    
    // ibSender->reqNewsArticle(12001,"BRFUPDN", "BRFUPDN$167e2c7c" , TagValueListSPtr(list));
    // std::this_thread::sleep_for(std::chrono::seconds(10));
    // return;
    // ibSender->reqNewsProviders();
    // News providers (3):
    // News provider [0] - providerCode: BRFG providerName: Briefing.com General Market Columns
    // News provider [1] - providerCode: BRFUPDN providerName: Briefing.com Analyst Actions
    // News provider [2] - providerCode: DJNL providerName: Dow Jones Newsletters
    int conId = 4391; // AMD;
    conId = 270639; // Intel
    conId = 76792991; //TSLA:76792991
    std::string provideCodes  = "BRFG+BRFUPDN+DJNL";
    ibSender->reqHistoricalNews(111, conId,provideCodes,"", "",1000, list);
    // std::this_thread::sleep_for(std::chrono::seconds(10));
    
    //Historical News. RequestId: 111, Time: 2024-01-26 14:00:49.0, ProviderCode: BRFUPDN, ArticleId: BRFUPDN$167e26be, Headline: {A:800015:L:en:K:-0.97:C:0.97}!Edward Jones downgraded Tesla (TSLA) to Hold
    // Historical News. RequestId: 111, Time: 2024-01-25 15:29:37.0, ProviderCode: BRFG, ArticleId: BRFG$167bcccd, Headline: {A:800015:L:en:K:0.84:C:0.8353081345558167}Tesla shareholders turning onto the exit ramp as growth reaches major speedbump in 2024

    // return;

    // Doesn't work.
    // Contract contract;
    // contract.symbol = "BRFG:BRFG_ALL";
    // contract.secType = "NEWS";
    // // Valid are: [BRFG, BRFUPDN, DJNL, WSHE, BZ, DJTOP]
    // contract.exchange = "BRFG";
    // ibSender->reqContractDetails(122, contract);
    // ibSender->reqNewsBulletins(true);
    std::this_thread::sleep_for(std::chrono::seconds(10));

    return;

}
