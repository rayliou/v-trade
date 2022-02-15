#pragma once
#include <mutex>
#include <semaphore>
using CountingSemaphore=std::counting_semaphore<100>;


#include "EClientSocket.h"

class EWrapper;
class EReaderSignal;

class IBTWSClient : public EClientSocket {
public:
	explicit IBTWSClient(CountingSemaphore *sem, EWrapper *ptr, EReaderSignal *pSignal = 0);
    virtual ~IBTWSClient() {}
	void reqContractDetails(int reqId, const Contract& contract);
private:
    std::mutex m_mutex;
    CountingSemaphore *m_pSemaphore;
};
