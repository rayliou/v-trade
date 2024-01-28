#pragma once
#include "VContract.h"
#include "common.h"
#include "CmdOption.h"
#include "V_IB_Sender.h"
#include "V_IB_Receiver.h"

extern V_IB_Receiver *g_pIBReceiver;
void v_news(CmdOption &cmd);
void v_scanner(CmdOption &cmd);
void v_tws_events(CmdOption &cmd);
void v_tws_history(CmdOption &cmd);