//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include <regex>
#include "BigTable.h"
#include "scenario.h"
#include "Scenario_v0.h"
#include "./3rd-party/JohansenCointegration/JohansenHelper.h"

// https://github.com/gabime/spdlog



class RunnerBT{
public:
    RunnerBT(const char * bigCsvPath,CmdOption & cmd): m_bigtable(bigCsvPath), m_cmdOption(cmd) {
        //m_log = spdlog::stderr_color_mt(typeid(*this).name());
        //m_log = spdlog::get("RunnerBT");
    }
    void t();
    void t(IndexData::iterator & start, IndexData::iterator &end );
    void run(const char * pairCsv, int continueDays = 1);
    void addScenarios_v0(const char * pairCsv, const char * conf=nullptr);
    void setupScenarios(IScenario * s);
    ~RunnerBT();

private:
    vector<IScenario *> m_scenarios;
    vector<string> m_symList;
    BigTable m_bigtable;
    static LogType  m_log;
    CmdOption & m_cmdOption;

};
LogType RunnerBT::m_log = spdlog::stderr_color_mt("RunnerBT");

RunnerBT::~RunnerBT (){
    for_each(m_scenarios.begin(), m_scenarios.end(),[] (IScenario *s) { delete s; });
    m_scenarios.clear();
}
void RunnerBT:: setupScenarios(IScenario * s){
    std::vector<SnapData> & snaps =  s->getSnapDataList() ;
    auto updateDate = [&] (SnapData & snap ) {
        auto it = m_bigtable.m_symbolToColIdx.find(snap.symbol);
        if(m_bigtable.m_symbolToColIdx.end() == it) {
            m_log->critical("Cannot get {} from bigtable, pair path: {}", snap.symbol, s->getConfPath());
            return;
        }
        snap.idx = it->second ;
        //snap.debug(m_log);
    };
    for_each(snaps.begin(), snaps.end(), updateDate);

}
void RunnerBT::addScenarios_v0(const char * pairCsv, const char * conf){
    Scenario_v0 *s = new Scenario_v0(pairCsv, m_cmdOption);
    setupScenarios(s);
    s->postSetup();
    m_scenarios.push_back(s);
}
void RunnerBT::run(const char * pairCsv, int continueDays){
    std::map<std::string, std::any> extEnv;
    this->addScenarios_v0(pairCsv);

    int N = m_symList.size();
    int totalCnt = N*(N-1)/2;
    //auto strRe =".*(20[-0-9]+)\\.(.*)/ols.csv";
    auto strRe =".*(20\\d\\d-\\d+-\\d+)\\.(.*)/ols.csv";
    std::regex re(strRe);
    std::smatch pieces_match;
    string var {pairCsv} ;
    auto ret = regex_match(var, pieces_match, re);
    if(!ret ||pieces_match.size() !=3) {
        m_log->critical("pairCsv {} does not match re {}", pairCsv, strRe);
        return;
    }
    auto date = pieces_match[1].str();
    auto group  = pieces_match[2].str();
    //vector<string> dateList;
    vector<time_t> dateList;
    auto tmStart = m_bigtable.strTime2time_t((date+" 23:59:59")  .c_str(),"%Y-%m-%d %H:%M:%S");
    //use the next trade day after the date which is set.
    auto itStart = find_if(m_bigtable.m_index.begin(),m_bigtable.m_index.end(),[&] (auto & i){ 
            return i.second >= tmStart;
    });
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

    //(*m_scenarios.begin())->debug(&m_log);
    for (auto it = itStart; it != itEnd; it++) {
        auto pos = it - m_bigtable.m_index.begin(); //not itStart
        auto refresh = [&] (IScenario * s ) {
            //s.updateData();
            //m_log->debug("pos:{}", pos);
            std::vector<SnapData> & snaps =  s->getSnapDataList() ;
            for(auto &snap : snaps) {
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
                snap.update(o,h,l,c,v,it->second);
            }
            s->runOneEpoch(*it, *itStart);
        };
        // for_each(std::execution::par_unseq, m_scenarios.begin(), m_scenarios.end(), refresh);
        for_each(m_scenarios.begin(), m_scenarios.end(), refresh);
    }
    for_each(m_scenarios.begin(), m_scenarios.end(), [&] (auto s){
            s->postOneEpoch(extEnv);
    });
}
void RunnerBT::t(IndexData::iterator & start, IndexData::iterator &end){
    auto n1 = "V";
    auto n2 = "MA";
    auto it = m_bigtable.m_symbolToColIdx.find(n1);
    if (it == m_bigtable.m_symbolToColIdx.end()) {
        m_log->critical("Cannot get {} from bigtable", n1);
        return;
    }
    int col_1 = it->second;
    it = m_bigtable.m_symbolToColIdx.find(n2);
    if (it == m_bigtable.m_symbolToColIdx.end()) {
        m_log->critical("Cannot get {} from bigtable", n2);
        return;
    }
    int col_2 = it->second;
    auto itCol1 = m_bigtable.m_columnData.begin() + col_1;
    auto itCol2 = m_bigtable.m_columnData.begin() + col_2;
    auto posStart = start - m_bigtable.m_index.begin();
    auto posEnd = end - m_bigtable.m_index.begin();
    DoubleMatrix xMat;
    xMat.resize(2);
    xMat[0].clear();
    xMat[1].clear();
    std::copy(itCol1->second.begin()+posStart,itCol1->second.begin()+posEnd,std::back_inserter(xMat[0]));
    std::copy(itCol2->second.begin()+posStart,itCol2->second.begin()+posEnd,std::back_inserter(xMat[1]));

    vector<MaxEigenData> outStats;
    DoubleVector eigenValuesVec;
    DoubleMatrix eigenVecMatrix;
    JohansenHelper johansenHelper(xMat);
    int days = round((end->second - start->second)/3600./24);
    for(int lags = 1; lags <=64; lags <<=1) {
        johansenHelper.DoMaxEigenValueTest(lags);
        int cointCount = johansenHelper.CointegrationCount();
        if (cointCount >0) {
            eigenValuesVec = johansenHelper.GetEigenValues();
            eigenVecMatrix = johansenHelper.GetEigenVecMatrix();
            auto beta_0 = eigenVecMatrix[0][0]/eigenVecMatrix[0][1];
            auto beta_1 = eigenVecMatrix[1][0]/eigenVecMatrix[1][1];
#if 0
            for (auto & ev : eigenVecMatrix ) {
                for (auto & c : ev ) {
                    cout << c << " ";
                }
                cout << endl;
            }
#endif
            m_log->debug("{}_{}cointCount:{};lambda_beta:{:.3f}:{:.3f},{:.3f}:{:.3f}\tlag:{}, days:{}\t{}:{}",
                    n1,n2
                    ,cointCount,eigenValuesVec[0],beta_0,eigenValuesVec[1],beta_1, lags,days,start->first, end->first);
        }
        outStats = johansenHelper.GetOutStats();
    }
}
void RunnerBT::t(){
#if 0
        s	i	m	st	halflife	HE	pair	p
    1.3900345809740500	-2.3424026533661100	-1.33214340879219E-14	0.39436858070784800	4.84	0.3274200600137500	TME_GTEC	0.0058521697013129
    18.825885929277600	-0.37935722984402000	1.20454485849993E-14	0.13865395586702800	5.35	0.2726943051716730	METX_IQ	0.0113077349412209
    14.1802997843113	-42.76635618329670	-6.63835730752094E-14	2.7019161074638800	22.39	0.43406404462359300	LU_FUTU	0.0148821258533774
    0.3079874795503250	1.7812422152179200	1.32878944832619E-14	0.18363037474109100	19.03	0.5305223630105	BZUN_LU	0.0155388896678845
#endif
    //detect data interval
    auto interval = (m_bigtable.m_index.begin() +1)->second - m_bigtable.m_index.begin()->second;
    int step = 3600/interval;

    for(int days =10; days <= 30; days +=10) {
        auto secs = days * 24 * 3600;
        auto s =  m_bigtable.m_index.begin()->second + secs;
        auto e =  (m_bigtable.m_index.end() -1)->second - 48 * 3600;
        auto itStart = find_if(m_bigtable.m_index.begin(),m_bigtable.m_index.end(),[&] (auto & i){ 
                return i.second >= s;
        });
        if(m_bigtable.m_index.end() == itStart) {
            m_log->trace("skip due to itStart find failed");
            continue;
        }
        auto itEnd = find_if(itStart,m_bigtable.m_index.end(),[&] (auto & i){ 
                return i.second >= e;
        });
        if(m_bigtable.m_index.end() == itEnd) {
            m_log->trace("skip due to itEnd find failed");
            continue;
        }
        //itStart as the 1st end for a range
        m_log->debug("{}:{}", itStart->first, (itEnd-1)->first);
        auto is = m_bigtable.m_index.begin();
        auto isPrev = is;
        //run it every 1 hr

        for(auto it = itStart; is< itStart &&it < itEnd; is++,it++) {
            if (is->second -isPrev->second > 3600 || is == itStart ) {
               // m_log->debug("interval {}, step: {}", interval, step);
                t(is,it);
                isPrev = is;
            }
        }
    }
}

int main(int argc, char * argv[]) {
    CmdOption cmd(argc,argv);
    spdlog::cfg::load_env_levels();
#if 0
    auto level = spdlog::level::level_enum::off;;
    auto s  = cmd.get("-v");
    if ( s != nullptr) {
        level = static_cast<spdlog::level::level_enum>(atoi(s));
        //trace debug info warn err critical off n_levels
    }
    spdlog::set_level(level);
#endif
    //spdlog::set_level(spdlog::level::xdebug);
    //spdlog::info("Welcome to spdlog!");
     auto    log = spdlog::stderr_color_mt("xconsole");
    if (argc <2){
        // cout << "csv file path is needed" << endl;
        log->error("CSV file path is needed");
        return 1;
    }
    auto mSsources  = cmd.getM("--m_src");
    if (mSsources.size() >0) {
        for (auto & srcPair : mSsources ) {
            auto ss = strSplit(srcPair, ':');
            RunnerBT c(ss[0].c_str(), cmd);
            c.t(); return 0;
            c.run(ss[1].c_str());
        }

    }
    else {
        auto srcPair = cmd.get("--src");
        auto ss = strSplit(srcPair, ':');
        RunnerBT c(ss[0].c_str(), cmd);
        c.t(); return 0;
        c.run(ss[1].c_str());
    }

    spdlog::info("{}", cmd.str());
    return 0;
}
