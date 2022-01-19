//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#include "common.h"

#include "Scenario_v0.h"
#include <fstream>

using namespace std;

Scenario_v0::Scenario_v0(const char * pairCsv, const char * conf) :m_log (spdlog::stdout_color_mt("Scenario_v0")) {
    //m_log = spdlog::stdout_color_mt("Scenario_v0");
    setupContractPairTrades(pairCsv);
    for_each(m_contracts.begin(),m_contracts.end(), [&] (ContractPairTrade & c ) {
        auto symbols = c.getSymbols();
        for_each(symbols.begin(), symbols.end(), [&] (const string  & symbol ) {
                m_snapDataVector.push_back(SnapData(symbol) );
        });

    });
    for_each(m_snapDataVector.begin(),m_snapDataVector.end(),[&] (auto s ) {
            s.debug(m_log);
    });
}
void Scenario_v0::setupContractPairTrades(const char *pairCsv) {
    std::ifstream myFile(pairCsv);
    if(!myFile.is_open()) throw std::runtime_error("Could not open file " + string(pairCsv));
    std::string line, colname;
    //map<string,int> colName2Idx ;
    vector<string> colNames ;
    if(myFile.good())
    {
        std::getline(myFile, line);
        std::stringstream ss(line);
        std::getline(ss, colname, ',');
        int i = 0;
        while(std::getline(ss, colname, ','))
        {
            colNames.push_back(colname);
            i++;
        }
    }
    while(std::getline(myFile, line))
    {
        std::getline(myFile, line);
        m_contracts.push_back(ContractPairTrade(colNames, line));
    }
    myFile.close();
    for_each(m_contracts.begin(),m_contracts.end(),[&] (auto s ) {
            s.debug(m_log);
    });
}
int main(int argc, char * argv[]) {
    Scenario_v0 s("/Users/henry/stock/env_study/2021-12-17.topV100_MC200/ols.csv");
    return 0;
}
