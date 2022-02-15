//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#pragma once
#include "common.h"

#include "ModelGroup.h"
#include "IBTWSApp.h"

class ModelLive: public ModelGroup {
public:
    ModelLive(CmdOption &cmd, IBTWSApp *ib);
    virtual ~ModelLive();
    virtual void run (bool *stopFlag);

private:
    static LogType  m_log;
    IBTWSApp * m_ib {nullptr};
    bool * m_stopFlag {nullptr};
    std::vector<SnapData *> m_ibSnapDataVct;
};
