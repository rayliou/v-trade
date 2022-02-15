//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#if 0
#include <string>
#include <fstream>
#include <vector>
#include <utility> // std::pair
#include <stdexcept> // std::runtime_error
#include <sstream> // std::stringstream
#include <iostream>
#include <tuple>
#include <map>
#include <time.h>
#endif
#include "SnapData.h"
#include "strategy.h"
#include <time.h>
#include <any>
                   //
class Money;
class IScenario {
public:
    IScenario(std::string name, CmdOption &cmd,SnapDataMap & snapDataMap)
        :m_name(name),m_cmdOption(cmd),m_snapDataMap(snapDataMap)  {
        auto var = m_cmdOption.get("--includes");
        if (nullptr != var) {
            auto symbols = strSplit(var,'_');
            std::for_each(symbols.begin(), symbols.end(), [&] (auto &s) {  m_includes.insert(s);} );
        }
        var  = m_cmdOption.get("--excludes");
        if (nullptr != var) {
            auto symbols = strSplit(var,',');
            std::for_each(symbols.begin(), symbols.end(), [&] (auto &s) {  m_excludes.insert(s);} );
        }
        m_log = spdlog::stderr_color_mt(m_name);
    }

    //predict begin & end for backtest.
    std::string getName() const  {return m_name;}
    virtual json getJResult () = 0;
    void setMoney(Money *m)  {m_money = m; }
    virtual void postSetup() = 0;
    virtual void runBT() = 0;
    virtual void debug(LogType *log) = 0;
    virtual ~IScenario() {}

protected:
    CmdOption & m_cmdOption;
    std::set<std::string> m_excludes;
    std::set<std::string> m_includes;
    SnapDataMap & m_snapDataMap;
    std::string m_name;
    Money *m_money {nullptr};
    LogType  m_log;
private:
    virtual void insertIncludes(const std::string &s) {
         m_includes.insert(s);
    }
    virtual void insertExcludes(const std::string &s) {
         m_excludes.insert(s);
    }
};
