#include <stdio.h>
#include "IBTWSApp.h"
#include "EPosixClientSocketPlatform.h"

void IBTWSApp::run() {
	const char * port = m_cmd.get("--port");
	const char * cId = m_cmd.get("--client_id");
	// if ( nullptr == port) {
	// 	throw std::runtime_error("--port arg needed.!!!");
	// }
	int p = nullptr == port ? 7496:atoi(port);
	int clientId = nullptr == cId ? 0:atoi(cId);
	connect("127.0.0.1", p,clientId);
	for(int i =0; i < 10; i++){
		if(isConnected()) {
			break;
		}
		m_log->trace("Connectting......");
        std::this_thread::sleep_for(std::chrono::seconds(1));
	}
	while(!m_stopFlag && isConnected()) {
		m_log->trace("m_stopFlag:{}", m_stopFlag);
		processMessages();
	}
	disconnect();
	return;
}
#if 0
int main(int argc, char * argv[]) {
    CmdOption cmd(argc,argv);
    spdlog::cfg::load_env_levels();
    IBTWSApp::runIBTWS();
    //IBTWSApp::runIBTWS();
    // Backtest bt(cmd);
    // bt.run(); return 0;

    spdlog::info("{}", cmd.str());
    return 0;
}
#endif

IBTWSApp::IBTWSApp (CmdOption &cmd, bool &stopFlag) 
    :m_cmd(cmd), m_stopFlag(stopFlag), m_pClient(new IBTWSClient(&m_semaphore,this, &m_osSignal)) {
    m_log = spdlog::stderr_color_mt("IBTWSApp");

 }
IBTWSApp::~IBTWSApp(){
// destroy the reader before the client
if( m_pReader )
    m_pReader.reset();

delete m_pClient;

}
bool IBTWSApp::connect(const char *host, int port, int clientId)
{
	ostringstream os;
	os << "IB:" << port << ":" << clientId;
    m_log = spdlog::stderr_color_mt(os.str());
	m_log->info("Connecting to {}:{} clientId: {}",!( host && *host) ? "127.0.0.1" : host, port, clientId); 
	//! [connect]
	bool bRes = m_pClient->eConnect( host, port, clientId, m_extraAuth);
	//! [connect]
	if (bRes) {
		m_log->info("Connected  to {}:{} clientId: {}",!( host && *host) ? "127.0.0.1" : host, port, clientId); 
		//! [ereader]
		m_pReader = std::unique_ptr<EReader>( new EReader(m_pClient, &m_osSignal) );
		m_pReader->start();
		//! [ereader]
	}
	else
		m_log->critical("Cannot Connect  to {}:{} clientId: {}",!( host && *host) ? "127.0.0.1" : host, port, clientId); 

	return bRes;
}

void IBTWSApp::disconnect() const {
    m_pClient->eDisconnect();
	m_log->info("Disconnected");
}

bool IBTWSApp::isConnected() const { return m_orderId > -1 &&  m_pClient->isConnected(); }
void IBTWSApp::setConnectOptions(const std::string& connectOptions) { m_pClient->setConnectOptions(connectOptions); }
void IBTWSApp::processMessages()
{
	time_t now = time(NULL);

    m_osSignal.waitForSignal();
	errno = 0;
	m_pReader->processMsgs();
}
void IBTWSApp::error(int id, int errorCode, const std::string& errorString, const std::string& advancedOrderRejectJson) {
	string sym =  (-1 == id)? "": m_snapDataVct->at(id)->symbol;

	if (!advancedOrderRejectJson.empty()) {
		m_log->error("Error. Id: {}:{}, Code: {}, Msg: {}, AdvancedOrderRejectJson: {}", id,sym, errorCode, errorString.c_str(), advancedOrderRejectJson.c_str());
	} else {
	m_log->error("Error. Id: {}:{}, Code: {}, Msg: {}", id,sym, errorCode, errorString.c_str());
	}
}

void IBTWSApp::nextValidId( OrderId orderId) {
	m_log->debug("Next Valid Id: {}", orderId);
	m_orderId = orderId;
	m_state = State::ST_ACCOUNTOPERATIONS;
    m_log->trace("End:{}", __PRETTY_FUNCTION__ );
}
void IBTWSApp::contractDetails( int reqId, const ContractDetails& contractDetails) {
     m_log->trace("Call:{}", __PRETTY_FUNCTION__ );
    if(pcontractDetails != nullptr && pcontractDetails(reqId,contractDetails)) {
        //stop
        return;
    }
	// auto tid = std::this_thread::get_id();
	m_semaphore.release();
	++m_snapUpdatedCnt;

    // m_log->trace("Start:{}", __PRETTY_FUNCTION__ );
	SnapData * s = m_snapDataVct->at(reqId);
	if (nullptr == s->ibContractDetails) {
		s->ibContractDetails =  std::make_unique<ContractDetails>();
	}
	*(s->ibContractDetails) = contractDetails;
	s->ibUpdated = true;
	// long conId = s->ibContractDetails->contract.conId;
	// string sym = s->ibContractDetails->contract.symbol;
	// m_log->debug("contractDetails: reqId,UpCnt {}/{} {},{}",reqId, m_snapUpdatedCnt.load(), sym, conId);
    // m_log->trace("End:{}", __PRETTY_FUNCTION__ );
}
void IBTWSApp::historicalDataEnd(int reqId, const std::string& startDateStr, const std::string& endDateStr) {
    if(phistoricalDataEnd != nullptr && phistoricalDataEnd(reqId,  startDateStr,  endDateStr)) {
        //stop
        return;
    }
	m_semaphore.release();
    m_log->trace("Call:{}", __PRETTY_FUNCTION__ );

}
void IBTWSApp::historicalData(TickerId reqId, const Bar& bar) {
    if(phistoricalData != nullptr && phistoricalData(reqId,  bar)) {
        //stop
        return;
    }
    m_log->trace("Call:{}", __PRETTY_FUNCTION__ );
	updateSnapByBar(reqId,bar);

}
void IBTWSApp::historicalDataUpdate(TickerId reqId, const Bar& bar) {
    m_log->trace("Call:{}", __PRETTY_FUNCTION__ );
	updateSnapByBar(reqId,bar);
}
void IBTWSApp::updateSnapByBar(TickerId reqId, const Bar& bar) {
	SnapData * s = m_snapDataVct->at(reqId);
	s->open = bar.open;
	s->close = bar.close;
	s->high = bar.high;
	s->low  = bar.low;
	s->volume = bar.volume;
	s->tm = atol(bar.time.c_str());
	s->debug(m_log);
}
inline double & getFielPtrinLiveData(LiveData &l, TickType t) {
	//  https://interactivebrokers.github.io/tws-api/tick_types.html
	switch (t) {
        case BID_SIZE:
		return l.bSize;
        case BID:
		return l.bid;
        case ASK:
		return l.ask;
        case ASK_SIZE:
		return l.aSize;
        case LAST:
		return l.last;
        case LAST_SIZE:
		return l.lSize;
        case HIGH:
		return l.hday;
        case LOW:
		return l.lday;
        case VOLUME:
		return l.vdayp;
        case CLOSE:
		return l.cprev;
        case OPEN:
		return l.oday;
		default: {
				string s;
				int nT = (int)t;

				s.resize(128, '\0');
				snprintf(s.data(), s.size(), "Unknow tick type: %d", nT); //static_cast<std::underlying_type_t<TickType>>(t));
				throw std::runtime_error(s);
		}
	}
}
void IBTWSApp::tickPrice( TickerId tickerId, TickType field, double price, const TickAttrib& attrib) {
	SnapData * s = m_snapDataVct->at(tickerId);
	getFielPtrinLiveData(s->liveData, field) = price;
	if( ASK != field) {
		return;
	}
	if ( std::fabs(s->liveData.bid - s->liveData.ask)/s->liveData.ask > 0.05 ) {
		return;
	}
	//FIXME fire strategy:
	s->debug(m_log);
    // m_log->trace("[{}]: {}, field:{}, price:{}", __PRETTY_FUNCTION__ , tickerId, field, price);
}
void IBTWSApp::tickSize(TickerId tickerId, TickType field, Decimal size) {
	SnapData * s = m_snapDataVct->at(tickerId);
	getFielPtrinLiveData(s->liveData, field) = decimalToDouble(size);
	// s->debug(m_log);
    // m_log->trace("[{}]: {}, field:{}, size:{}", __PRETTY_FUNCTION__ , tickerId, field, decimalToDouble(size));
}
void IBTWSApp::tickSnapshotEnd( int reqId) {
	// SnapData * s = m_snapDataVct->at(reqId);
	// m_semaphore.release();
    // m_log->trace("[{}]: {}", __PRETTY_FUNCTION__ , reqId);
	// // m_pClient->reqMktData(reqId++, s->ibContractDetails.contract, "", true, true,TagValueListSPtr()); 
}
void IBTWSApp::tickString(TickerId tickerId, TickType tickType, const std::string& value) {
	// SnapData * s = m_snapDataVct->at(tickerId);
    // m_log->trace("[{}]: {}, {}, {}", __PRETTY_FUNCTION__ , tickerId, tickType, value);

}
