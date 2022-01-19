//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include "BigTable.h"
#include "scenario.h"
#include "3rd-party/spdlog/include/spdlog/spdlog.h"
#include "3rd-party/spdlog/include/spdlog/sinks/stdout_color_sinks.h"

// https://github.com/gabime/spdlog

class RunnerBT{
public:
    RunnerBT(const char * bigCsvPath): m_bigtable(bigCsvPath){
        m_log = spdlog::stdout_color_mt("RunnerBT");
    }
    void run();
    void addScenarios_v0(const char * conf);
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
    std::vector<SnapData> & snaps =  s->getSymbolList() ;
    auto updateDate = [&] (SnapData & snap ) {
        auto it = m_bigtable.m_symbolToColIdx.find(snap.symbol);
        assert(m_bigtable.m_symbolToColIdx.end() != it);
        snap.idx = it->second;
        m_log->debug("snap.idx:{},",snap.idx);
    };
    for_each(snaps.begin(), snaps.end(), updateDate);
}
void RunnerBT::addScenarios_v0(const char * conf){
    Scenario_v0 *s = new Scenario_v0();
    setupScenarios(s);
    m_scenarios.push_back(s);
}
void RunnerBT::run(){
    this->addScenarios_v0("");

    int N = m_symList.size();
    int totalCnt = N*(N-1)/2;
    auto itStart = m_bigtable.m_index.begin();
    auto itEnd   = m_bigtable.m_index.end();
    for (auto it = itStart; it != itEnd; it++) {
        auto pos = it - itStart;
        auto refresh = [&] (IScenario * s ) {
            //s.updateData();
            std::vector<SnapData> & snaps =  s->getSymbolList() ;
            auto updateDate = [&] (SnapData & snap ) {
                m_log->debug("idx:{},",*it);
                for (int i =0; i < m_bigtable.m_fieldsNum; i++) {
                    auto col = m_bigtable.m_columnData[snap.idx +i];
                    assert( col.first == snap.symbol);
                    snap.close = col.second[pos];
                }
            };
            for_each(snaps.begin(), snaps.end(), updateDate);
            s->execute();
        };
        // for_each(std::execution::par_unseq, m_scenarios.begin(), m_scenarios.end(), refresh);
        for_each(m_scenarios.begin(), m_scenarios.end(), refresh);
    }
    #if 0
    int cnt = 0;
    for (int i =0; i < N; i++){
        for (int j =i+1; j < N; j++){
            auto n1 = m_symList.at(i);
            auto n2 = m_symList.at(j);
            // auto start = 1;
            // auto end = 1;
            for (int k = 1; k <= 4; k++){
                auto idxPosRange = m_bigtable.getIndexRange(endDate,7*k);
                printf("[%d/%d][%s-%s] [%s:%ld][%s:%ld]\n", cnt,totalCnt ,n1.c_str(),n2.c_str(),
                 idxPosRange.first->first.c_str(), idxPosRange.first - m_bigtable.m_index.begin()
                 ,idxPosRange.second->first.c_str(), idxPosRange.second - m_bigtable.m_index.begin()
                 );
                int idxStart = idxPosRange.first - m_bigtable.m_index.begin();
                int idxEnd = idxPosRange.second - m_bigtable.m_index.begin();

                auto matchN1 = [&](const ColumnData::value_type &v){ return v.first  == n1 + "_close"; };
                auto matchN2 = [&](const ColumnData::value_type &v){ return v.first  == n2 + "_close"; };
                auto itN1 = std::find_if(m_bigtable.m_columnData.begin(),m_bigtable.m_columnData.end(),matchN1);
                auto itN2 = std::find_if(m_bigtable.m_columnData.begin(),m_bigtable.m_columnData.end(),matchN2);
                #if 0
                printf("\t[%s-%s][%f,%f]\n", 
                    itN1->first.c_str(),
                    itN2->first.c_str(),
                    itN1->second[0],
                    itN2->second[0]
                );
                #endif
                double *X = itN1->second.data() + idxStart;
                double *Y = itN2->second.data() + idxStart;
                int len = idxEnd - idxStart;




            }

            // #float p = this->coint(n1,n2,start,end);
                // v = {'pair': f'{k1}_{k2}', 'p': p, 'pmin':pMin, 'start_of_pmin':start_of_pmin,}# 'plist': pList }
                // merge........


            cnt ++;

        }
    }
    #endif

}





int main(int argc, char * argv[]) {
    spdlog::info("Welcome to spdlog!");
     auto    log = spdlog::stdout_color_mt("xconsole");
    if (argc <2){
        // cout << "csv file path is needed" << endl;
        log->error("CSV file path is needed");

        return 1;
    }
    auto filePath  = argv[1];
    const char * endDate = argv[2];
    // const char * endDate = "2022-01-13 08:09:0";
    RunnerBT c(filePath);
    c.run();
    return 0;
}
