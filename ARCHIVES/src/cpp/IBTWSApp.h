﻿#pragma once
#include <atomic>
#include <functional>
#include "common.h"
#include "DefaultEWrapper.h"

#include "EReaderOSSignal.h"
#include "EReader.h"

#include "IBTWSClient.h"
#include "SnapData.h"
// https://interactivebrokers.github.io/tws-api/client_wrapper.html#ewrapper_impl

#include <memory>
#include <vector>
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




class EClientSocket;
class IBTWSApp: public DefaultEWrapper {
public:
	void run();
    IBTWSApp (CmdOption &cmd, bool &stopFlag);
    virtual ~IBTWSApp();
    bool connect(const char * host, int port, int clientId = 0);
	void disconnect() const;
	bool isConnected() const;
	OrderId getOrderId() const { return m_orderId;}
    void waitConnected();
    void setConnectOptions(const std::string& connectOptions);
	void processMessages();
	IBTWSClient * getClient () const {return m_pClient;};
	int getSnapUpdateCnt () const {return m_snapUpdatedCnt.load();};
	void resetSnapUpdateCnt () {m_snapUpdatedCnt =0;  };
	void setSnapDataVct(vector<SnapData *>  * snapDataVct) {m_snapDataVct = snapDataVct; }
    void setJThread(std::jthread * j) {m_jthread = j; }
    using PcontractDetails = std::function<bool ( int reqId, const ContractDetails& contractDetails)>;
	using PhistoricalData=std::function<bool (TickerId reqId, const Bar& bar)>;
	using PhistoricalDataEnd=std::function<bool (int reqId, const std::string& startDateStr, const std::string& endDateStr) >;

    void setCallback(PcontractDetails p) {pcontractDetails =p;}
    void setCallback(PhistoricalData p) {phistoricalData =p;}
    void setCallback(PhistoricalDataEnd p) {phistoricalDataEnd =p;}

	void setReceiver(Ohlcv::ValuesOhlcv * v,Ohlcv::TimeMapOhlcv *m) {m_emptyValuesOhlcv = v;m_timeMapOhlcv =m;}

private:

    virtual void error(int id, int errorCode, const std::string& errorString, const std::string& advancedOrderRejectJson) ;
	virtual void nextValidId( OrderId orderId);
	virtual void contractDetails( int reqId, const ContractDetails& contractDetails);
	PcontractDetails pcontractDetails {nullptr};

	virtual void historicalData(TickerId reqId, const Bar& bar);
	PhistoricalData phistoricalData {nullptr};
	virtual void historicalDataEnd(int reqId, const std::string& startDateStr, const std::string& endDateStr);
	PhistoricalDataEnd phistoricalDataEnd {nullptr};
	virtual void historicalDataUpdate(TickerId reqId, const Bar& bar);

	virtual void tickPrice( TickerId tickerId, TickType field, double price, const TickAttrib& attrib);
	virtual void tickSize(TickerId tickerId, TickType field, Decimal size);
	virtual void tickSnapshotEnd( int reqId);
	virtual void tickString(TickerId tickerId, TickType tickType, const std::string& value);
#if 0

	virtual void tickOptionComputation( TickerId tickerId, TickType tickType, int tickAttrib, double impliedVol, double delta, double optPrice, double pvDividend, double gamma, double vega, double theta, double undPrice){throw std::runtime_error(__PRETTY_FUNCTION__); }
	virtual void tickGeneric(TickerId tickerId, TickType tickType, double value){throw std::runtime_error(__PRETTY_FUNCTION__); }
	virtual void tickEFP(TickerId tickerId, TickType tickType, double basisPoints, const std::string& formattedBasisPoints, double totalDividends, int holdDays, const std::string& futureLastTradeDate, double dividendImpact, double dividendsToLastTradeDate){throw std::runtime_error(__PRETTY_FUNCTION__); }
	virtual void orderStatus( OrderId orderId, const std::string& status, Decimal filled, Decimal remaining, double avgFillPrice, int permId, int parentId, double lastFillPrice, int clientId, const std::string& whyHeld, double mktCapPrice){throw std::runtime_error(__PRETTY_FUNCTION__); }
	virtual void openOrder( OrderId orderId, const Contract&, const Order&, const OrderState&){throw std::runtime_error(__PRETTY_FUNCTION__); }
	virtual void openOrderEnd(){throw std::runtime_error(__PRETTY_FUNCTION__); }
#endif
virtual void managedAccounts( const std::string& accountsList);
virtual void pnl(int reqId, double dailyPnL, double unrealizedPnL, double realizedPnL);
virtual void pnlSingle(int reqId, Decimal pos, double dailyPnL, double unrealizedPnL, double realizedPnL, double value);


private:
	void updateSnapByBar(TickerId reqId, const Bar& bar);
    	//! [socket_declare]
	EReaderOSSignal m_osSignal {2000}; //2 secs;
	IBTWSClient * m_pClient;
	//! [socket_declare]
	State m_state;

	std::unique_ptr<EReader> m_pReader;

	time_t m_sleepDeadline {0};
	OrderId m_orderId {-1};
	std::string m_accountName;
    bool m_extraAuth {false};
	std::string m_bboExchange;
    LogType  m_log;
	CmdOption & m_cmd;
	bool & m_stopFlag;
	std::vector<SnapData *>  * m_snapDataVct {nullptr};
	std::atomic<int> m_snapUpdatedCnt {0};
    CountingSemaphore m_semaphore {50};
    std::thread::id m_IBTWSApp_id;
    std::jthread * m_jthread {nullptr};
	Ohlcv::ValuesOhlcv  * m_emptyValuesOhlcv {nullptr};
	Ohlcv::TimeMapOhlcv  *m_timeMapOhlcv {nullptr};
};