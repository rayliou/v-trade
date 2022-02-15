//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
//
#pragma once
#include "common.h"
#include <execution>
#include "ModelGroup.h"


class ModelBacktest : public ModelGroup {
public:
    ModelBacktest(CmdOption &cmd);
    virtual ~ModelBacktest();
    virtual void run(bool *stopFlag) ;

private:
    static LogType  m_log;
};
