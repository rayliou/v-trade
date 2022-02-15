﻿#include "IBTWSClient.h"
using namespace std;

IBTWSClient::IBTWSClient(CountingSemaphore *sem, EWrapper *ptr, EReaderSignal *pSignal)
    :m_pSemaphore(sem),
    EClientSocket(ptr, pSignal) {

}
void IBTWSClient::reqContractDetails(int reqId, const Contract& contract) {
    m_pSemaphore->acquire();
    scoped_lock lock(m_mutex);

    EClientSocket::reqContractDetails(reqId, contract);
}
