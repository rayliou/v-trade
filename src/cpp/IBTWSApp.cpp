#include "IBTWSApp.h"
#include "EClientSocket.h"
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
	while(!m_stopFlag && isConnected()) {
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

IBTWSApp::IBTWSApp (CmdOption &cmd, bool &stopFlag) :m_cmd(cmd), m_stopFlag(stopFlag), m_pClient(new EClientSocket(this, &m_osSignal)) {

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

bool IBTWSApp::isConnected() const { return m_pClient->isConnected(); }
void IBTWSApp::setConnectOptions(const std::string& connectOptions) { m_pClient->setConnectOptions(connectOptions); }
void IBTWSApp::processMessages()
{
	time_t now = time(NULL);

    m_osSignal.waitForSignal();
	errno = 0;
	m_pReader->processMsgs();
}
void IBTWSApp::error(int id, int errorCode, const std::string& errorString, const std::string& advancedOrderRejectJson) {
	if (!advancedOrderRejectJson.empty()) {
		m_log->error("Error. Id: {}, Code: {}, Msg: {}, AdvancedOrderRejectJson: {}", id, errorCode, errorString.c_str(), advancedOrderRejectJson.c_str());
	} else {
	m_log->error("Error. Id: {}, Code: {}, Msg: {}", id, errorCode, errorString.c_str());
	}
}

void IBTWSApp::nextValidId( OrderId orderId) {
	m_log->debug("Next Valid Id: {}", orderId);
	m_orderId = orderId;
	m_state = State::ST_ACCOUNTOPERATIONS;
}