/* Copyright (C) 2019 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
 * and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable. */

#pragma once
#include "EWrapper.h"
#include "EReaderOSSignal.h"
#include "EReader.h"

#include <memory>
#include <vector>
#include "common.h"
#include "CmdOption.h"
#include "V_IB_Sender.h"
#include "VContract.h"
enum State {
	ST_CONNECT,
	ST_TICKDATAOPERATION,
	ST_TICKDATAOPERATION_ACK,
	ST_TICKOPTIONCOMPUTATIONOPERATION,
	ST_TICKOPTIONCOMPUTATIONOPERATION_ACK,
	ST_DELAYEDTICKDATAOPERATION,
	ST_DELAYEDTICKDATAOPERATION_ACK,
	ST_MARKETDEPTHOPERATION,
	ST_MARKETDEPTHOPERATION_ACK,
	ST_REALTIMEBARS,
	ST_REALTIMEBARS_ACK,
	ST_MARKETDATATYPE,
	ST_MARKETDATATYPE_ACK,
	ST_HISTORICALDATAREQUESTS,
	ST_HISTORICALDATAREQUESTS_ACK,
	ST_OPTIONSOPERATIONS,
	ST_OPTIONSOPERATIONS_ACK,
	ST_CONTRACTOPERATION,
	ST_CONTRACTOPERATION_ACK,
	ST_MARKETSCANNERS,
	ST_MARKETSCANNERS_ACK,
	ST_FUNDAMENTALS,
	ST_FUNDAMENTALS_ACK,
	ST_BULLETINS,
	ST_BULLETINS_ACK,
	ST_ACCOUNTOPERATIONS,
	ST_ACCOUNTOPERATIONS_ACK,
	ST_ORDEROPERATIONS,
	ST_ORDEROPERATIONS_ACK,
	ST_OCASAMPLES,
	ST_OCASAMPLES_ACK,
	ST_CONDITIONSAMPLES,
	ST_CONDITIONSAMPLES_ACK,
	ST_BRACKETSAMPLES,
	ST_BRACKETSAMPLES_ACK,
	ST_HEDGESAMPLES,
	ST_HEDGESAMPLES_ACK,
	ST_TESTALGOSAMPLES,
	ST_TESTALGOSAMPLES_ACK,
	ST_FAORDERSAMPLES,
	ST_FAORDERSAMPLES_ACK,
	ST_FAOPERATIONS,
	ST_FAOPERATIONS_ACK,
	ST_DISPLAYGROUPS,
	ST_DISPLAYGROUPS_ACK,
	ST_MISCELANEOUS,
	ST_MISCELANEOUS_ACK,
	ST_CANCELORDER,
	ST_CANCELORDER_ACK,
	ST_FAMILYCODES,
	ST_FAMILYCODES_ACK,
	ST_SYMBOLSAMPLES,
	ST_SYMBOLSAMPLES_ACK,
	ST_REQMKTDEPTHEXCHANGES,
	ST_REQMKTDEPTHEXCHANGES_ACK,
	ST_REQNEWSTICKS,
	ST_REQNEWSTICKS_ACK,
	ST_REQSMARTCOMPONENTS,
	ST_REQSMARTCOMPONENTS_ACK,
	ST_NEWSPROVIDERS,
	ST_NEWSPROVIDERS_ACK,
	ST_REQNEWSARTICLE,
	ST_REQNEWSARTICLE_ACK,
	ST_REQHISTORICALNEWS,
	ST_REQHISTORICALNEWS_ACK,
	ST_REQHEADTIMESTAMP,
	ST_REQHEADTIMESTAMP_ACK,
	ST_REQHISTOGRAMDATA,
	ST_REQHISTOGRAMDATA_ACK,
	ST_REROUTECFD,
	ST_REROUTECFD_ACK,
	ST_MARKETRULE,
	ST_MARKETRULE_ACK,
    ST_PNL,
    ST_PNL_ACK,
    ST_PNLSINGLE,
    ST_PNLSINGLE_ACK,
    ST_CONTFUT,
    ST_CONTFUT_ACK,
	ST_PING,
	ST_PING_ACK,
    ST_REQHISTORICALTICKS,
    ST_REQHISTORICALTICKS_ACK,
    ST_REQTICKBYTICKDATA,
    ST_REQTICKBYTICKDATA_ACK,
	ST_WHATIFSAMPLES,
	ST_WHATIFSAMPLES_ACK,
	ST_IDLE,
	ST_IBKRATSSAMPLE,
	ST_IBKRATSSAMPLE_ACK,
	ST_WSH,
	ST_WSH_ACK
};

//! [ewrapperimpl]
class V_IB_Receiver : public EWrapper
{
//! [ewrapperimpl]
public:
	void run();
    V_IB_Sender * getClient() {return m_pClient;}
	void waitConnected();
	void setJThread(std::jthread * jth){m_jthread = jth;}
	//Counting when requesting a batch of data
	int getRemainingCnt() const  {return m_remaining_cnt;}
	void setRemainingCnt(int cnt) {m_remaining_cnt = cnt;}
public:
    V_IB_Receiver(CmdOption &cmd, bool &stopFlag,VectorOfPtrVContract * vcontract_vector);
	~V_IB_Receiver();

	void setConnectOptions(const std::string&);
	void processMessages();

private:
	void switchState();

public:

	bool connect(const char * host, int port, int clientId = 0);
	void disconnect() const;
	bool isConnected() const;

private:
    void pnlOperation();
    void pnlSingleOperation();
	void tickDataOperation();
	void tickOptionComputationOperation();
	void delayedTickDataOperation();
	void marketDepthOperations();
	void realTimeBars();
	void marketDataType();
	void historicalDataRequests();
	void optionsOperations();
	void accountOperations();
	void orderOperations();
	void ocaSamples();
	void conditionSamples();
	void bracketSample();
	void hedgeSample();
	void contractOperations();
	void marketScanners();
	void fundamentals();
	void bulletins();
	void testAlgoSamples();
	void financialAdvisorOrderSamples();
	void financialAdvisorOperations();
	void testDisplayGroups();
	void miscelaneous();
	void reqFamilyCodes();
	void reqMatchingSymbols();
	void reqMktDepthExchanges();
	void reqNewsTicks();
	void reqSmartComponents();
	void reqNewsProviders();
	void reqNewsArticle();
	void reqHistoricalNews();
	void reqHeadTimestamp();
	void reqHistogramData();
	void rerouteCFDOperations();
	void marketRuleOperations();
	void continuousFuturesOperations();
    void reqHistoricalTicks();
    void reqTickByTickData();
	void whatIfSamples();
	void ibkratsSample();
	void wshCalendarOperations();

	void reqCurrentTime();

public:
	// events
	#include "EWrapper_prototypes.h"


private:
	void printContractMsg(const Contract& contract);
	void printContractDetailsMsg(const ContractDetails& contractDetails);
	void printContractDetailsSecIdList(const TagValueListSPtr &secIdList);
	void printBondContractDetailsMsg(const ContractDetails& contractDetails);

private:
	//! [socket_declare]
	EReaderOSSignal m_osSignal;
	V_IB_Sender * m_pClient;
	//! [socket_declare]
	State m_state;
	time_t m_sleepDeadline;

	OrderId m_orderId {-1};
	std::unique_ptr<EReader> m_pReader;
    bool m_extraAuth;
	std::string m_bboExchange;
private:
	int m_remaining_cnt {0};
    LogType  m_log;
	CmdOption & m_cmd;
	bool & m_stopFlag;
	VectorOfPtrVContract *m_vcontract_vector {nullptr};
	// std::atomic<int> m_snapUpdatedCnt {0};
    CountingSemaphore m_semaphore {50};
    std::thread::id m_IBTWSApp_id;
    std::jthread * m_jthread {nullptr};
	// Ohlcv::ValuesOhlcv  * m_emptyValuesOhlcv {nullptr};
	// Ohlcv::TimeMapOhlcv  *m_timeMapOhlcv {nullptr};
};


