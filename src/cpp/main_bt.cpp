//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include <regex>
#include "BigTable.h"
#include "scenario.h"
#include "Scenario_v0.h"

// https://github.com/gabime/spdlog

class RunnerBT{
public:
    RunnerBT(const char * bigCsvPath): m_bigtable(bigCsvPath){
        m_log = spdlog::stdout_color_mt(typeid(*this).name());
    }
    void run(const char * pairCsv, int continueDays = 1);
    void addScenarios_v0(const char * pairCsv, const char * conf=nullptr);
    void setupScenarios(IScenario * s);
    ~RunnerBT();

private:
    vector<IScenario *> m_scenarios;
    vector<string> m_symList;
    BigTable m_bigtable;
    std::shared_ptr<spdlog::logger> m_log;

};

RunnerBT::~RunnerBT (){
    for_each(m_scenarios.begin(), m_scenarios.end(),[] (IScenario *s) { delete s; });
    m_scenarios.clear();
}
void RunnerBT:: setupScenarios(IScenario * s){
    std::vector<SnapData> & snaps =  s->getSnapDataList() ;
    auto updateDate = [&] (SnapData & snap ) {
        auto it = m_bigtable.m_symbolToColIdx.find(snap.symbol);
        assert(m_bigtable.m_symbolToColIdx.end() != it);
        snap.idx = it->second * m_bigtable.m_fieldsNum;
        snap.debug(m_log);
    };
    for_each(snaps.begin(), snaps.end(), updateDate);

}
void RunnerBT::addScenarios_v0(const char * pairCsv, const char * conf){
    Scenario_v0 *s = new Scenario_v0(pairCsv);
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



    (*m_scenarios.begin())->debug(&m_log);
    for (auto it = itStart; it != itEnd; it++) {
        auto pos = it - itStart;
        auto refresh = [&] (IScenario * s ) {
            //s.updateData();
            std::vector<SnapData> & snaps =  s->getSnapDataList() ;
            auto updateDate = [&] (SnapData & snap ) {
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
                //m_log->debug("{},{},{}", itCol->first,snap.symbol, snap.close);
            };
            for_each(snaps.begin(), snaps.end(), updateDate);
            //s->debug(&m_log);
            s->execute(*it, *itStart);
        };
        // for_each(std::execution::par_unseq, m_scenarios.begin(), m_scenarios.end(), refresh);
        for_each(m_scenarios.begin(), m_scenarios.end(), refresh);
    }

    for_each(m_scenarios.begin(), m_scenarios.end(), [&] (auto s){
            s->summary(extEnv);
    });
}

int main(int argc, char * argv[]) {
    spdlog::set_level(spdlog::level::err);
    spdlog::set_level(spdlog::level::debug);
    spdlog::info("Welcome to spdlog!");
     auto    log = spdlog::stdout_color_mt("xconsole");
    if (argc <2){
        // cout << "csv file path is needed" << endl;
        log->error("CSV file path is needed");

        return 1;
    }
    auto filePath  = argv[1];
    const char * pairCsv = argv[2];
    //const char * endDate = argv[2];
    // const char * endDate = "2022-01-13 08:09:0";
    RunnerBT c(filePath);
    c.run(pairCsv);
    return 0;
}
