#include "IBTWSClient.h"
using namespace std;

IBTWSClient::IBTWSClient(CountingSemaphore *sem, EWrapper *ptr, EReaderSignal *pSignal)
    :m_pSemaphore(sem),
    EClientSocket(ptr, pSignal) {

}
void IBTWSClient::reqContractDetails(int reqId, const Contract& contract) {
    scoped_lock lock(m_mutex);
    m_pSemaphore->acquire();

    EClientSocket::reqContractDetails(reqId, contract);
}
