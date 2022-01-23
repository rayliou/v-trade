//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include <any> // std::stringstream
#include <sstream> // std::stringstream
#include <regex>
#include "contract.h"

class SnapData;
class Money {
public:
    Money () {}
    virtual bool isMoneyAvailable(double cashAmt, double marginAmt = 0, float cashRate = 0.5, float marginRate =0.5 ) const  {
        double amount = cashAmt * cashRate + marginAmt * marginRate;
        bool ret =  amount < (m_cash - m_margin_freeze);
        m_log->debug("C:[{}];M:[{}];amount:{} = cashAmt {} * cashRate {} + marginAmt {} * marginRate {},ret:{} "
        ,m_cash,m_margin_freeze
        ,amount,cashAmt,cashRate,marginAmt, marginRate,ret
        );
         return ret;
    }
    virtual void withdraw(double cashAmt, double marginAmt) {
        m_cash -= cashAmt;
        m_margin_freeze += marginAmt;
    }
    virtual void deposit(double cashAmt, double marginAmt) {
        m_cash += cashAmt;
        m_margin_freeze -= marginAmt;
    }
    virtual double getTotalCash() const { return m_cash;}
    virtual double getTotalMarginFreezed() const { return m_margin_freeze;}
    virtual void subCash(double amount) { m_cash -= amount; }
    virtual ~Money() {}
private:
    double m_cash {100000.};
    double m_margin_freeze {0};
    static LogType  m_log;
};

class ContractPairTrade : public IContract {
public:
    ContractPairTrade (csv::CSVRow& row, Money &m);
    std::vector<std::string>  getSymbols() const;
    time_t getOpenTime() const { return m_openTime;}

    void  setAvailable(bool available) { m_isAvailable = available; }
    bool  isAvailable() { return  m_isAvailable;} 

    void debug(LogType log) ;
    void newPosition(float x, float y, bool buyN1,float z0, const time_t &t, const std::map<std::string, std::any> &ext);
    float  closePosition(float x, float y, const std::map<std::string, std::any> & ext);

public:
    float m_slope,m_intercept ,m_mean, m_std, m_halflife, m_p,m_pmin;
    float m_z {0};
    float m_zPrev {0};
    float m_z0 {0};
    std::string m_ext, m_n1,m_n2;
    std::pair<std::string, std::string> m_symbolsPair; 
    // s,i,m,st,halflife,pair,p,pmin,ext
    SnapData * m_snap1;;
    SnapData *  m_snap2;;
    Position m_position1;
    Position m_position2;
private:
    //ContractPairTrade () = delete;
   // ContractPairTrade (const ContractPairTrade &c) = delete;
    Money  *m_money {nullptr};
private:
    static LogType  m_log;
    bool m_isAvailable {false};
    time_t  m_openTime;
};

