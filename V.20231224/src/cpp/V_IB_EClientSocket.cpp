#include "V_IB_EClientSocket.h"
using namespace std;

V_IB_EClientSocket::V_IB_EClientSocket(CountingSemaphore *sem, EWrapper *ptr, EReaderSignal *pSignal)
    :m_pSemaphore(sem),m_log(spdlog::stderr_color_mt("V_IB_EClientSocket"))
    ,EClientSocket(ptr, pSignal) {

}
void V_IB_EClientSocket::speedControl(std::list<time_t> &callList, int maxCalls, int seconds){
    maxCalls --;
    int total = callList.size();
    while(total >= maxCalls) {
        m_log->trace("speedControl: total: {} >= maxCall: {} per {} secs", total, maxCalls, seconds);
        auto tm = time(NULL);
        while (total > 0 &&  (tm - *callList.begin()) > seconds ) {
            callList.pop_front();
            total --;
        }
        std::this_thread::sleep_for(std::chrono::microseconds(100));
    }
    callList.push_back(time(NULL));
}
void V_IB_EClientSocket::reqContractDetails(int reqId, const Contract& contract) {
    m_pSemaphore->acquire();
    scoped_lock lock(m_mutex);

    EClientSocket::reqContractDetails(reqId, contract);
}
void V_IB_EClientSocket::reqHistoricalData(TickerId tickerId, const Contract& contract,
                                const std::string& endDateTime, const std::string& durationStr,
                                const std::string&  barSizeSetting, const std::string& whatToShow,
                                int useRTH, int formatDate, bool keepUpToDate, const TagValueListSPtr& chartOptions) {
    m_pSemaphore->acquire();
    speedControl(m_callsCurSec, 50,1);
    scoped_lock lock(m_mutex);
    EClient::reqHistoricalData(tickerId, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate, keepUpToDate,chartOptions);
}

void V_IB_EClientSocket::reqMktData(TickerId tickerId, const Contract& contract, const std::string& genericTicks, bool snapshot, bool regulatorySnaphsot, const TagValueListSPtr& mktDataOptions) {
    // speedControl(m_callsCurSec, 50,1);
    m_pSemaphore->acquire();
    EClientSocket::reqMktData(tickerId,contract,genericTicks,snapshot,regulatorySnaphsot, mktDataOptions);
}
