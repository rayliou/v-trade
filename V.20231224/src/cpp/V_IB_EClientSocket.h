#pragma once
#include <list>
#include <mutex>
#include <semaphore>
#include "common.h"

using CountingSemaphore=std::counting_semaphore<200>;


#include "EClientSocket.h"

class EWrapper;
class EReaderSignal;

class V_IB_EClientSocket : public EClientSocket {
public:
	explicit V_IB_EClientSocket(CountingSemaphore *sem, EWrapper *ptr, EReaderSignal *pSignal = 0);
    virtual ~V_IB_EClientSocket() {}
	void reqContractDetails(int reqId, const Contract& contract);
    void reqHistoricalData(TickerId tickerId, const Contract& contract,
                                const std::string& endDateTime, const std::string& durationStr,
                                const std::string&  barSizeSetting, const std::string& whatToShow,
                                int useRTH, int formatDate, bool keepUpToDate, const TagValueListSPtr& chartOptions);

    void reqMktData(TickerId tickerId, const Contract& contract,
                         const std::string& genericTicks, bool snapshot, bool regulatorySnaphsot, const TagValueListSPtr& mktDataOptions);

private:
    void speedControl(std::list<time_t> &callList, int maxCalls = 50, int seconds = 1);
private:
    std::mutex m_mutex;
    CountingSemaphore *m_pSemaphore;
    std::list<time_t> m_callsCurSec;
    LogType  m_log;
};
