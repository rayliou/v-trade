//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#include "common.h"
#include <execution>
#include "scenario.h"
#include "ModelLive.h"

LogType ModelLive::m_log = spdlog::stderr_color_mt("ModelLive");
ModelLive::ModelLive(CmdOption &cmd,IBTWSApp *ib)
    :ModelGroup(cmd), m_ib(ib) {

}
ModelLive::~ModelLive() {
    m_log->trace("Call:{}", __PRETTY_FUNCTION__ );
}
void ModelLive::run(bool *stopFlag) {
    const int TIMEOUT_CONTRACTS = 30;
    m_stopFlag = stopFlag;
    updateSnapDataContracts(TIMEOUT_CONTRACTS);
    updateSnapDataLive(3600 * 6.5);

}
void ModelLive::updateSnapDataContracts(int timeout) {
    IBTWSClient *ibClient = m_ib->getClient();
    m_ibSnapDataVct.clear();
    m_ib->setSnapDataVct(&m_ibSnapDataVct);
    m_ib->resetSnapUpdateCnt();

    int reqId = 0;
    for (auto &[k, v]: m_snapDataMap) {
        Contract contract;
        contract.symbol = k;
        contract.secType = "STK";
        contract.currency = "USD";
        contract.exchange = "SMART";
        v.ibUpdated = false;
        m_ibSnapDataVct.push_back(&v);
        ibClient->reqContractDetails(reqId++, contract);
    }
    //wait
    auto tmStart = time(NULL);
    int total = m_ibSnapDataVct.size();
    while ( m_ib->getSnapUpdateCnt() < total && (time(NULL) - tmStart) < timeout) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
        m_log->trace("[{}/{}]:Waiting for reqContractDetails",m_ib->getSnapUpdateCnt() , total);
    }
    if ( m_ib->getSnapUpdateCnt() < total) {
        ostringstream so;
        for (auto &[k, s]: m_snapDataMap) {
            if(!s.ibUpdated) {
                so << k << ",";
            }
        }
        m_log->warn("Symbols that didn't update {}", so.str());
    }
    for (auto &[k, s]: m_snapDataMap) {
        if(!s.ibUpdated) {
            continue;
        }
        long conId = s.ibContractDetails->contract.conId;
        string sym = s.ibContractDetails->contract.symbol;
        m_log->debug("contractDetails: {},{}", sym, conId);
    }
}
void ModelLive::updateSnapDataLive(int timeout) {
    IBTWSClient *ibClient = m_ib->getClient();
    m_ibSnapDataVct.clear();
    m_ib->setSnapDataVct(&m_ibSnapDataVct);
    m_ib->resetSnapUpdateCnt();

    int reqId = 0;
    for (auto &[k, v]: m_snapDataMap) {
        // if(50 <= reqId) { break; }
        if (nullptr ==  v.ibContractDetails) {
            m_log->critical("updateSnapDataLive:ib contract is null:{}", k);
            continue;
        }
        Contract &c = v.ibContractDetails->contract;

        v.ibUpdated = false;
        m_ibSnapDataVct.push_back(&v);
        // https://interactivebrokers.github.io/tws-api/classIBApi_1_1EClient.html#aad87a15294377608e59aec1d87420594
        ibClient->reqHistoricalData(reqId++, c, "", "200 S", "5 secs", "MIDPOINT", 0, 2/*1 :string, 2: seconds,  */ ,/*keepUpToDate = */ false,TagValueListSPtr()); 

    }
    std::this_thread::sleep_for(std::chrono::seconds(timeout));
    //wait
    // auto tmStart = time(NULL);
    // int total = m_ibSnapDataVct.size();
    // while ( m_ib->getSnapUpdateCnt() < total && (time(NULL) - tmStart) < timeout) {
    //     std::this_thread::sleep_for(std::chrono::seconds(1));
    //     m_log->trace("[{}/{}]:Waiting for reqContractDetails",m_ib->getSnapUpdateCnt() , total);
    // }
    // if ( m_ib->getSnapUpdateCnt() < total) {
    //     ostringstream so;
    //     for (auto &[k, s]: m_snapDataMap) {
    //         if(!s.ibUpdated) {
    //             so << k << ",";
    //         }
    //     }
    //     m_log->warn("Symbols that didn't update {}", so.str());
    // }
    // for (auto &[k, s]: m_snapDataMap) {
    //     if(!s.ibUpdated) {
    //         continue;
    //     }
    //     long conId = s.ibContractDetails->contract.conId;
    //     string sym = s.ibContractDetails->contract.symbol;
    //     m_log->debug("contractDetails: {},{}", sym, conId);
    // }
}