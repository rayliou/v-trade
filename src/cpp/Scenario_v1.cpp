//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#include "common.h"

#include <regex>
#include "Scenario_v1.h"
#include <fstream>
#include <numeric>


using namespace std;

LogType Scenario_v1::m_out = spdlog::stdout_color_mt("stdout");

//https://stackoverflow.com/questions/18939869/how-to-get-the-slope-of-a-linear-regression-line-using-c
template<typename T>
T slope(const std::vector<T>& x, const std::vector<T>& y) {
    const auto n    = x.size();
    const auto s_x  = std::accumulate(x.begin(), x.end(), 0.0);
    const auto s_y  = std::accumulate(y.begin(), y.end(), 0.0);
    const auto s_xx = std::inner_product(x.begin(), x.end(), x.begin(), 0.0);
    const auto s_xy = std::inner_product(x.begin(), x.end(), y.begin(), 0.0);
    const auto a    = (n * s_xy - s_x * s_y) / (n * s_xx - s_x * s_x);
    return a;
}

Scenario_v1::Scenario_v1(std::string name, CmdOption &cmd,SnapDataMap & snapDataMap,const char * modelFilePath, BigTable & bigtable)
    : IScenario(name,cmd, snapDataMap),m_bigtable(bigtable) {
    //m_log = spdlog::stderr_color_mt(typeid(*this).name());
    std::ifstream is(modelFilePath);
    for(string line; std::getline(is,line); ) {
        json j = json::parse(line);
        m_contracts.push_back(ContractPairTrade(j, m_money,m_name));

    }
    //construct snap data list
    for(auto &c : m_contracts) {
        auto symbols = c.getSymbols();
            for_each(symbols.begin(), symbols.end(), [&] (const string  & symbol ) {
                auto it = m_bigtable.m_symbolToColIdx.find(symbol);
                if(m_bigtable.m_symbolToColIdx.end() == it) {
                    m_log->critical("Cannot get {} from bigtable, pair path: {}", symbol, modelFilePath);
                    return;
                }
                auto idx = it->second ;
                auto itSnap = m_snapDataMap.find(symbol);
                if (itSnap == m_snapDataMap.end()) {
                    m_snapDataMap.insert({symbol,SnapData(symbol,idx)});
                }
            });
        auto itSnap = m_snapDataMap.find(c.m_n1);
        c.m_snap1 = &(itSnap->second);
        itSnap = m_snapDataMap.find(c.m_n2);
        c.m_snap2 = &(itSnap->second);

    }
    //get group & model time
    auto strRe =".*(20\\d\\d-\\d+-\\d+)\\.(.*)/js_coint.json";
    std::regex re(strRe);
    std::smatch pieces_match;
    string var {modelFilePath} ;
    auto ret = regex_match(var, pieces_match, re);
    if(!ret ||pieces_match.size() !=3) {
        m_log->critical("modelFilePath {} does not match re {}", modelFilePath, strRe);
        return;
    }
    auto date = pieces_match[1].str();
    auto group  = pieces_match[2].str();
    //vector<string> dateList;
    vector<time_t> dateList;
    m_modelTime = m_bigtable.strTime2time_t((date+" 23:59:59")  .c_str(),"%Y-%m-%d %H:%M:%S");

    postSetup();
    //debug();
}
void Scenario_v1::postSetup() {
    auto isSnapAvailable  = []  (auto * ptr) -> bool { return ptr != nullptr && ptr->idx != -1;  };
    if ( m_includes.size() >0) {
        for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            auto it1 = m_includes.find(c.m_n1);
            auto it2 = m_includes.find(c.m_n2);
            auto available =  ( it1 != m_includes.end() && it2 != m_includes.end());
            available = available && isSnapAvailable(c.m_snap1) && isSnapAvailable(c.m_snap2);
            c.setAvailable(available);
        });
    }
    else if ( m_excludes.size() >0) {
        for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            auto it1 = m_excludes.find(c.m_n1);
            auto it2 = m_excludes.find(c.m_n2);
            auto available =  ( it1 == m_excludes.end() && it2 == m_excludes.end());
            available = available && isSnapAvailable(c.m_snap1) && isSnapAvailable(c.m_snap2);
            c.setAvailable(available);
        });
    }
    else {
        for(auto & c: m_contracts) {
            auto  available = isSnapAvailable(c.m_snap1) && isSnapAvailable(c.m_snap2);
            c.setAvailable(available);
        }
    }
    auto endIt = remove_if(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
            bool ret =  !c.isAvailable();
            //ret |= c.m_he > 0.45;
            //ret |= c.m_halflife > 6 *3600;
            m_log->info("{}_{}:{}", c.m_n1, c.m_n2, (ret?"Remove unused":"Keep"));
            return ret;
    });
    m_contracts.erase(endIt,m_contracts.end());
}
void Scenario_v1::debug(LogType *log) {
    if (nullptr == log) {
        log  = &m_log;
    }
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto &c ) {
            c.debug(m_log);
            if(c.isAvailable()) {
                c.m_snap1->debug(*log);
                c.m_snap2->debug(*log);
            }
    });
}
void Scenario_v1::preOneEpoch(const std::map<std::string, std::any>& ext) {
}
void Scenario_v1::postOneEpoch(const std::map<std::string, std::any>& ext) {

    vector<IContract *> contracts;
    for (auto &c:m_contracts ) {
        auto p  = c.getProfit();
        if(p == 0) {
            continue;
        }
        contracts.push_back(&c);
    }
    // transform(m_contracts.begin(),m_contracts.end(),back_inserter(contracts),[&] (auto & c ) -> auto { return &c; });
    sort(contracts.begin(),contracts.end(), [&] (IContract *aC, IContract *bC) -> auto {
        auto a  = aC->getProfit();
        auto b  = bC->getProfit();
        if (a == b) {
            return aC->getName() < bC->getName();
        }
        if ( a == 0){
            return true;
        }
        if ( b == 0){
            return false;
        }
        return a <b;
    });
    for (auto c :contracts ) {
        ContractPairTrade *p = dynamic_cast<ContractPairTrade *>(c);
        int duration = p->getTransDuration();
        int halflife = p->m_halflife ;
        m_out->info("[{}]\tTrans:{},profit:{:.2f}\tP:{:04.2f},Pmin:{:04.2f},HE:{:04.2f}\tduration: {:1d} mins, halflife:{:1d} mins", p->getName(),p->getTransactionNum(), p->getProfit()
        ,p->m_p,p->m_pmin, p->m_he
        , duration/60, halflife/60
        //, p->m_ext
        );
    }
    // for_each(m_contracts.begin(),m_contracts.end(),[&] (auto & c ) {
    //     m_log->debug("[{}_{}] Profit:{} " , c.m_n1,c.m_n2, c.getProfit());
    // });
    vector<float> v;
    transform(contracts.begin(),contracts.end(), back_inserter(v),  [&] (auto & c ) {
        return c->getProfit();
    });
    auto sum = std::accumulate(v.begin(), v.end(), 0.0);
    auto mean = sum / v.size();
    auto sq_sum = std::inner_product(v.begin(), v.end(), v.begin(), 0.0);
    auto stdev = std::sqrt(sq_sum / v.size() - mean * mean);
    m_out->info("Total:{}, mean: {}, std:{},sum:{}", v.size(),mean, stdev, sum);

}
void Scenario_v1::updateSnapDataByBigTable(int pos) {
    auto tm = m_bigtable.m_index[pos].second;
    for (auto &[symbol, snap]:m_snapDataMap) {
        if( !snap.isAvailable()) {
            continue;
        }
        auto itCol = m_bigtable.m_columnData.begin() + snap.idx;
        //close	high	low	open	volume
        auto c  = itCol->second[pos];
        itCol ++;
        auto h  = itCol->second[pos];
        itCol ++;
        auto l  = itCol->second[pos];
        itCol ++;
        auto o  = itCol->second[pos];
        itCol ++;
        auto v  = itCol->second[pos];
        snap.update(o,h,l,c,v,tm);
    }
}
void Scenario_v1::strategy() {
    for_each(m_contracts.begin(), m_contracts.end(), [&](auto &c){
        c.setRank(3);
    });
}
void Scenario_v1::rank(vector<ContractPairTrade *> &contracts) {
    contracts.clear();
    for ( auto & c: m_contracts) {
        if( c.getRank() == 0) {
            continue;
        }
        contracts.push_back(&c);
    }
    sort(contracts.begin(),contracts.end(), [&] (ContractPairTrade * aC, ContractPairTrade * bC) -> bool {
        //FIXME
        return aC->getRank() < bC->getRank();
    });
    return ;
}
void Scenario_v1::executeTrades(vector<ContractPairTrade *> &contracts) {
    for (ContractPairTrade *c: contracts) {
    }
    contracts.clear();
}
void Scenario_v1::runBT() {
    const int contractsLimit  = 3;
    const int timeOut = 10; // 10 seconds.
    float maxBTdays = 1.5;
    //use the next trade day after the date which is set.
    auto itStart = find_if(m_bigtable.m_index.begin(),m_bigtable.m_index.end(),[&] (auto & i){ 
            return i.second >= m_modelTime;
    });
    if (itStart == m_bigtable.m_index.end()) {
        m_log->critical("Big table error, cannot find index time gt {}", m_modelTime);
        exit(1);
    }
    int intervalSecs = (m_bigtable.m_index.begin() +1)->second - m_bigtable.m_index.begin()->second;
    auto maxBasrs = 1 + maxBTdays * 6.5 * 3600 / intervalSecs;
    int pos = itStart - m_bigtable.m_index.begin();
    int end = pos + maxBasrs;
    m_log->info("BT time range: {} to {}",m_bigtable.m_index[pos].first, m_bigtable.m_index[end-1].first);
    vector<ContractPairTrade *>  contracts;
    time_t tm;
    time(&tm);
    auto tmPrev = tm;
    for (; pos < end; pos++) {
        updateSnapDataByBigTable(pos);
        strategy();
        rank(contracts);
        time(&tm);
        if (tm - tmPrev > timeOut || contracts.size() > contractsLimit ) {
            executeTrades(contracts);
            tmPrev = tm;
        }
        //-  analysis and log
    }
    //last piece.
    executeTrades(contracts);
    debug();
    //for (auto &[symbol, snap]:m_snapDataMap) { snap.debug(m_log); }
#if 0
    struct tm tPrev;
    memset(&tPrev, 0, sizeof(tPrev));
    //remove duplicate/uniq
    for_each(itStart,m_bigtable.m_index.end(), [&] (auto & i){
            struct tm t;
            localtime_r(&(i.second), &t);
            if(t.tm_year > tPrev.tm_year ||t.tm_mon > tPrev.tm_mon ||t.tm_mday > tPrev.tm_mday ) {
                dateList.push_back(i.second);
            }
            tPrev = t;
    });
    auto itEnd   = m_bigtable.m_index.end();
    if (dateList.size() >=2) {
        itEnd = find_if(itStart,m_bigtable.m_index.end(),[&] (auto & i){ 
                //m_log->debug(i.first);
                return i.second > dateList[continueDays];
        });
    }

    for_each(m_scenarios.begin(), m_scenarios.end(), [&] (auto s){
            s->preOneEpoch(extEnv);
    });
#endif


}
