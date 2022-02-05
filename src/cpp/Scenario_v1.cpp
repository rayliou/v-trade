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
    : IScenario(name,cmd, snapDataMap),m_bigtable(bigtable),m_modelFilePath(modelFilePath) {
    //m_log = spdlog::stderr_color_mt(typeid(*this).name());
    m_outTraceDataPath = cmd.get("--out_trace_data");
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
    m_log->info("Start:{}", __PRETTY_FUNCTION__ );
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
            //m_log->info("{}_{}:{}", c.m_n1, c.m_n2, (ret?"Remove unused":"Keep"));
            return ret;
    });
    m_contracts.erase(endIt,m_contracts.end());
    string allPairs = std::accumulate(m_contracts.begin(),m_contracts.end(), string(""), [&](const string & a, auto &b) -> string {
        return a + b.getName() + ",";
    });
    m_log->info("All pairs:{}", allPairs);

    float stdRateH {0.} ,stdRateL { std::numeric_limits<float>::infinity() };
    for (ContractPairTrade & c :  m_contracts) {
        stdRateH = std::max(stdRateH, c.std_rate);
        stdRateL = std::min(stdRateL, c.std_rate);
    }
    float coeff = std::sqrt(stdRateH*stdRateL) ;
    for (ContractPairTrade & c :  m_contracts) {
        c.setMoneyCoeff(coeff);
    }
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
void Scenario_v1::updateSnapDataByBigTable(int pos, SnapData &snap) {
    auto tm = m_bigtable.m_index[pos].second;
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
void Scenario_v1::updateSnapDataByBigTable(int pos) {
    for (auto &[symbol, snap]:m_snapDataMap) {
        if( !snap.isAvailable()) {
            continue;
        }
        updateSnapDataByBigTable(pos,snap);
    }
}
void Scenario_v1::rank(std::vector<ContractPairTrade *> &openCtrcts,std::vector<ContractPairTrade *> &closeCtrcts) {
    openCtrcts.clear();
    closeCtrcts.clear();
    for ( auto & c: m_contracts) {
        strategy(c);
        if( c.getRank() == 0) {
            continue;
        }
        openCtrcts.push_back(&c);
        closeCtrcts.push_back(&c);
    }
    sort(openCtrcts.begin(),openCtrcts.end(), [&] (ContractPairTrade * aC, ContractPairTrade * bC) -> bool {
        //FIXME
        return aC->getRank() < bC->getRank();
    });
    sort(closeCtrcts.begin(),closeCtrcts.end(), [&] (ContractPairTrade * aC, ContractPairTrade * bC) -> bool {
        //FIXME
        return aC->getRank() < bC->getRank();
    });
    return ;
}
void Scenario_v1::executeTrades(std::vector<ContractPairTrade *> &openCtrcts,std::vector<ContractPairTrade *> &closeCtrcts) {
    for (ContractPairTrade *c: openCtrcts) {
    }
    for (ContractPairTrade *c: closeCtrcts) {
    }
    openCtrcts.clear();
    closeCtrcts.clear();
}
void Scenario_v1::preRunBT() {
    m_log->info("Start:{}", __PRETTY_FUNCTION__ );
    auto itEnd = find_if(m_bigtable.m_index.begin(),m_bigtable.m_index.end(),[&] (auto & i){ 
            return i.second >= m_modelTime;
    });
    if (itEnd == m_bigtable.m_index.end()) {
        m_log->critical("Big table error, cannot find index time gt {}", m_modelTime);
        exit(1);
    }
    int end = itEnd - m_bigtable.m_index.begin();
    //int intervalSecs = (m_bigtable.m_index.begin() +1)->second - m_bigtable.m_index.begin()->second;
    //auto maxBasrs = 1 + maxBTdays * 6.5 * 3600 / intervalSecs;
    //int pos = itStart - m_bigtable.m_index.begin();
    //int end = pos + maxBasrs;
     //using WinDiffDataType=std::list<DiffData>;
    for ( auto & c: m_contracts) {
        int pos = end - c.getHalfLifeBars();
        WinDiffDataType winDiff;
        for(;pos != end ;pos++) {
            DiffData d;
            updateSnapDataByBigTable(pos, *c.m_snap1);
            updateSnapDataByBigTable(pos, *c.m_snap2);
            calContractDiffData(c,d);
            winDiff.push_back(d,false);
        }
        c.initWindowByHistory(std::move(winDiff));
        //m_log->warn("windiff size:{}",winDiff.size()); exit(0);
    }
}
void Scenario_v1::postRunBT() {
    m_log->info("Start:{}", __PRETTY_FUNCTION__ );
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
        int halflife = p->getHalfLifeSecs();
        m_out->info("[{}]\tTrans:{},profit:{:.2f}\tP:{:04.2f},Pmin:{:04.2f},HE:{:04.2f},std_rate:{:04.2f},slopeDiffRate:{:04.2f}\tduration: {:1d} mins, halflife:{:1d} mins", p->getName(),p->getTransactionNum(), p->getProfit()
        ,p->m_p,p->m_pmin, p->getHurstExponent(),p->std_rate
        , p->getSlopeDiffRate()
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
    m_out->warn("sum\t{}\tTotal:{}, mean: {}\tstd:{},{}"
            ,sum,  v.size(),mean, stdev, m_modelFilePath);

    m_log->info("End:{}", __PRETTY_FUNCTION__ );
}
void Scenario_v1::runBT() {
    m_log->info("Start:{}", __PRETTY_FUNCTION__ );
    //runEpoch
    preRunBT();
    const int contractsLimit  = 3;
    const int timeOut = 10; // 10 seconds.
                            //
    float maxBTdays = 1.5;
    //use the next trade day after the date which is set.
    auto itStart = find_if(m_bigtable.m_index.begin(),m_bigtable.m_index.end(),[&] (auto & i){ 
            return i.second >= m_modelTime;
    });
    if (itStart == m_bigtable.m_index.end()) {
        m_log->critical("Big table error, cannot find index time gt {}", m_modelTime);
        exit(1);
    }
    m_startTime = itStart->second;
    int intervalSecs = (m_bigtable.m_index.begin() +1)->second - m_bigtable.m_index.begin()->second;
    int maxBasrs = 1 + maxBTdays * 6.5 * 3600 / intervalSecs;
    int leftBars = m_bigtable.m_index.end() - itStart;
    maxBasrs = std::min(maxBasrs, leftBars);
    int pos = itStart - m_bigtable.m_index.begin();
    int end = pos + maxBasrs;
    m_log->info("BT time range: {} to {}",m_bigtable.m_index[pos].first, m_bigtable.m_index[end-1].first);

    std::vector<ContractPairTrade *> openCtrcts;
    std::vector<ContractPairTrade *> closeCtrcts;
    auto tm = m_bigtable.m_index[pos].second;
    auto tmPrev = tm;

    m_pOutWinDiff = &cout;
    m_pOutWinDiff  = nullptr;
    ofstream of;
    if ( nullptr != m_outTraceDataPath &&  m_outTraceDataPath[0] != 0 ) {
        of.open(m_outTraceDataPath); 
        m_pOutWinDiff = &of; 
        *m_pOutWinDiff << "pair," << m_contracts.begin()->getWinDiffDataFields() << endl;
    }

    for (; pos < end; pos++) {
        updateSnapDataByBigTable(pos);
        //evalue strategy & sort by rank
        rank(openCtrcts,closeCtrcts);
        tm = m_bigtable.m_index[pos].second;
        if (tm - tmPrev > timeOut || openCtrcts.size() > contractsLimit || closeCtrcts.size() >contractsLimit ) {
            executeTrades(openCtrcts,closeCtrcts);
            tmPrev = tm;
        }
        //-  analysis and log
    }
    //last piece.
    executeTrades(openCtrcts,closeCtrcts);
    //for (auto &[symbol, snap]:m_snapDataMap) { snap.debug(m_log); }
    postRunBT();
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
void Scenario_v1::calContractDiffData(ContractPairTrade &c, DiffData &d) {
    auto tm = std::max(c.m_snap1->tm,c.m_snap2->tm );
    auto slope = c.m_slope;
    auto C1 = c.m_snap1->close;
    auto C2 = c.m_snap2->close;
    auto H1 = c.m_snap1->high;
    auto H2 = c.m_snap2->high;
    auto L1 = c.m_snap1->low;
    auto L2 = c.m_snap2->low;

    float p1 = (C1 + H1 +L1)/3.;
    float p2 = (C2 + H2 +L2)/3.;

    auto v1 = c.m_snap1->volume;
    auto v2 = c.m_snap2->volume;
    d.diff =  slope * p1 - p2;
    d.tm = tm;
    d.p1 = p1;
    d.p2 = p2;
}
void Scenario_v1::strategy(ContractPairTrade &c) {
    /*
     *
    //m_slopeDiffRate
     *
     *
     */
    DiffData d;
    calContractDiffData(c, d);
    //cal Z
    WinDiffDataType & winDiff = c.updateWindowBySnap(d,m_pOutWinDiff);
    WinDiffDataType::reverse_iterator rbegin = winDiff.rbegin();
    WinDiffDataType::reverse_iterator it = rbegin;
    // to 15:30
    time_t curTime  = rbegin->tm;
    auto leftTime =   m_startTime + 3600 * 5 -  curTime;
    int halfLifeSeconds = c.getHalfLifeSecs();

    int curPosition = c.curPositionDirection() ;
    if(curPosition !=0 ) { // 1 -> n1 is - , n2 is +
        // 1 n1 too high, sell n1 & buy n1
        // -1 n1 too low, buy n1 & sell n2
        //////////// Trailing make the profit run..........
        float stopDiff = c.getStopDiff();
        auto it = rbegin;
        float d0 = it->diff;
        float d1 = (++it)->diff;

        float d_stN =  (it->diff - (it->mean + curPosition * it->std)) *curPosition;
        float d_stF = (it->diff - (it->mean - curPosition * it->std)) *curPosition ;
        float d_stF2 = (it->diff - (it->mean - 2* curPosition * it->std)) *curPosition ;
        float d_stF3 = (it->diff - (it->mean - 3 *curPosition * it->std)) *curPosition ;
        float d_m = (it->diff - it->mean) *curPosition ;
        float d_mH = (it->diff - it->mean_half) *curPosition ;


        if ((d0 -d1) *curPosition < 0) {
            m_log->trace("TR-[{}]:{}\t{}\t[Trailing diff] diff~stopDiff:[{}-{}]",winDiff.getTickCnt(), c.getName(), rbegin->toString(), rbegin->diff, stopDiff);
            if (c.m_diffFarest == 0 || (d0 - c.m_diffFarest  ) *curPosition < 0) {
                c.m_diffFarest = d0;
            }
            // 3,2,1 std.
            //FIXME
            c.m_hasCrossedStd_near  |=  d_stN < 0;
            c.m_hasCrossedStd_far   |=  d_stF < 0;
            c.m_hasCrossedStd_far2  |=  d_stF2 < 0;
            c.m_hasCrossedStd_far3  |=  d_stF3 < 0;
            c.m_hasCrossedMean |=  d_m < 0;
            c.m_hasCrossedMean_half  |= d_mH < 0;
            return;
        }
        //////////// Stop 0
        if ((rbegin->diff -stopDiff ) *curPosition > 0) {
            m_log->warn("S-[{}]:{}\t{}\t[Stop diff reached] diff~stopDiff:[{}-{}]",winDiff.getTickCnt(), c.getName(), rbegin->toString(), rbegin->diff, stopDiff);
            c.closePosition(rbegin->p1, rbegin->p2);
            return;
        }
        //////////// Time out
        auto hold = rbegin->tm - c.getOpenTime();
        if (halfLifeSeconds < hold ) {
            m_log->warn("T-[{}]:{}\t{}\t[Timeout ] HL,holdTime:{},{} secs  ",winDiff.getTickCnt(), c.getName(), rbegin->toString(),halfLifeSeconds,hold);
            c.closePosition(rbegin->p1, rbegin->p2);
            return;
        }
        //reverse . touch any condition or line.
        it = rbegin;
        list <pair<bool, float>> lines  { 
                {c.m_hasCrossedStd_far3, d_stF3}
                ,{c.m_hasCrossedStd_far2, d_stF2}
                ,{c.m_hasCrossedStd_far, d_stF}
                ,{c.m_hasCrossedMean, d_m}
                 };
        for ( auto & [touch, diff2] : lines ) {
            if(touch && diff2 > 0) {
                m_log->warn("P-[{}]:{}\t{}\t[Profit with far std or mean] diff~stopDiff:[{}-{}]",winDiff.getTickCnt(), c.getName(), rbegin->toString(), rbegin->diff, stopDiff);
                c.closePosition(rbegin->p1, rbegin->p2);
                return;
            }
        }
        it = rbegin;
        float ddLimit = 2 *rbegin->avg_diffdiff;
        // if (c.m_hasCrossedMean_half && (d0 -c.m_diffFarest) *curPosition > ddLimit) {
        if (true) {
            // m_log->warn("P-[{}]:{}\t{}\t[Profit.move is too fast] d0~d1~avgDD:{}~{}~{}",winDiff.getTickCnt(), c.getName(), rbegin->toString(),d0,d1, ddLimit);
            // c.closePosition(rbegin->p1, rbegin->p2);
            ///////////////////// d_m vs d_mH.
            list <pair<bool, float>> lines2  { 
                    {c.m_hasCrossedStd_near, d_stN}
                    ,{c.m_hasCrossedMean_half, d_mH}
                    };
            lines2.sort();
            for ( auto & [touch, diff2] : lines2 ) {
                if(touch && diff2 > 0) {
                    m_log->warn("P-[{}]:{}\t{}\t[Profit with mean half or near std] diff~stopDiff:[{}-{}]",winDiff.getTickCnt(), c.getName(), rbegin->toString(), rbegin->diff, stopDiff);
                    c.closePosition(rbegin->p1, rbegin->p2);
                    return;
                }
            }
            // return;
        }
        m_log->trace("W-[{}]:{}\t{}\t[do nothing] diff~stopDiff:[{}-{}]",winDiff.getTickCnt(), c.getName(), rbegin->toString(), rbegin->diff, stopDiff);
    }
    else { //0 position
        if (halfLifeSeconds > leftTime ) {
            m_log->trace("I-[{}]:{}\t{}\t[max trade time has reached] halfLifeSeconds,lefttime {},{} mins",winDiff.getTickCnt(), c.getName(), rbegin->toString(), halfLifeSeconds/60,leftTime/60);
            return ;
        }
        if (curTime - m_startTime <  SKIP_1ST_SECS) {
            m_log->trace("I-[{}]:{}\t{}\t[Skipe 1st time range {} secs ] ",winDiff.getTickCnt(), c.getName(), rbegin->toString(), SKIP_1ST_SECS);
            return ;
        }
        it = rbegin;
        float d0 = it->std - it->sm_std_20 ;
        float d1 = (++it)->std - it->sm_std_20 ;
        // std decrease.
        // narrow std band. do nothing.
        #if 0
        if (d0 <0 && d1 > 0) {
            c.m_cntCrsDwn_sm_std_20 ++;
            return;
        }
        if (c.m_cntCrsDwn_sm_std_20 ==0) {
            m_log->trace("W-[{}]:{}\t{}\t[Wait for std decrease]",winDiff.getTickCnt(), c.getName(), rbegin->toString() );
            return;
        }
        #endif

        float stdPercent =  (rbegin->std - rbegin->stdL) /(rbegin->stdH - rbegin->stdL) ;
        /////// on create on the top
        if ( stdPercent < THRESHOLD_STD_PERCENT) {
            m_log->trace("W-[{}]:{}\t{}\t[Wait for std increase] stdPercent:{}",winDiff.getTickCnt(), c.getName(), rbegin->toString(), stdPercent);
            return;
        }
        m_log->debug("R-[{}]:{}\t{}\t[Std ready] stdPercent:{}",winDiff.getTickCnt(), c.getName(), rbegin->toString(), stdPercent);
        it = rbegin;
        //cross
        auto crossIn = [&] () -> int {
            // -1, 0, 1
            int ret = 0;
            auto it = rbegin;
            float z0 = it->z;
            float z1 = (++it)->z;
            float z2 = (++it)->z;
            float z3 = (++it)->z;
            float z4 = (++it)->z;
            bool z_down = z1 <= z2 && z2 <= z3 ; // && z3 <= z4;
            bool z_up = z1 >= z2 && z2 >= z3; // && z3 >= z4;

            // positive cross in
            ret = (z0 >= THRESHOLD_Z_L  &&  z0 <= THRESHOLD_Z_H  && z1 > THRESHOLD_Z_H &&  z_down) ? 1 : (
                    //negative cross in check
                    (z0 <= -THRESHOLD_Z_L  &&  z0 >= -THRESHOLD_Z_H  && z1< -THRESHOLD_Z_H &&  z_up)? -1:0
                    );
            m_log->trace("\t[{}]:{}\t{}\t[Cross in check] z0:{},z1:{}, ret:{}",winDiff.getTickCnt(), c.getName(), rbegin->toString(), z0,z1,ret);
             
            return ret;
        };
        int retCross = crossIn();
        // 1 n1 too high, sell n1 & buy n1
        // -1 n1 too low, buy n1 & sell n2
        if (retCross != 0) {
            m_log->warn("\t[{}]:{}\t{}\t[Z cross in]",winDiff.getTickCnt(), c.getName(), rbegin->toString());
            // stop diff. direction
            float stopDiff  = rbegin->diff + STD_RATE_STOPDIFF * rbegin->std *retCross;
            c.newPosition(retCross,stopDiff, rbegin->p1, rbegin->p2);
            return;
        }
#if 0
        auto std  = rbegin->std;
        for(int i =0; ++it,i< MAXBARS_STD_CHECK; i++) {
            if (std > it->std) {
                m_log->trace("[{}]:{}\t{}\t[Wait for std decrease]",winDiff.getTickCnt(), c.getName(), rbegin->toString());
                return;
            }
        }
#endif
        //m_log->debug("[{}]:{}\t{}\t[Std ready]",winDiff.getTickCnt(), c.getName(), rbegin->toString());
        //check cross into.
    }
    c.setRank(3);
}
