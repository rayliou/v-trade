//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include <any> // std::stringstream
#include <sstream> // std::stringstream
#include <regex>
#include "contract.h"
#include "BigTable.h"

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
    virtual ~Money() {}
private:
    virtual void subCash(double amount) { m_cash -= amount; }
    double m_cash {100000.};
    double m_margin_freeze {0};
    static LogType  m_log;
};

struct DiffData {
    float diff;
    float mean {0.};
    float std {-1.};
    float z {0.};
    time_t tm;
    std::ostream & outFieldsNames(std::ostream &out) const {
        out << "tm,diff,mean,std,z";
        return out;
    }
    std::ostream & outValues(std::ostream &out) const {
        out << tm << "," << diff << "," << mean << "," << std << "," << z;
        return out;
    }
    void debug(LogType log, int i, int totalCnt, std::string name = "") {
        std::ostringstream os;
        outFieldsNames(os);
        os << ":";
        outValues(os);
        auto v = os.str();
        log->debug("{}\tdiffData:[{}/{}]:{}", name,i, totalCnt,v);
    }

};
using WinDiffDataType=std::list<DiffData>;

class ContractPairTrade : public IContract {
public:
    ContractPairTrade (json& j,Money &m, std::string &slopeName);

    //ContractPairTrade (csv::CSVRow& row, Money &m);

    std::vector<std::string>  getSymbols() const;
    time_t getOpenTime() const { return m_openTime;}

    void  setAvailable(bool available) { m_isAvailable = available; }
    bool  isAvailable() { return  m_isAvailable;} 

    void debug(LogType log) ;
    void newPosition(float x, float y, bool buyN1,float z0, const time_t &t, const std::map<std::string, std::any> &ext);
    float  closePosition(float x, float y,const time_t &t, const std::map<std::string, std::any> & ext);
    virtual string getName() const { return m_name; }
    virtual void setRank(float rank)  {m_rank = rank;}
    virtual float getRank() const { return m_rank;}
    virtual int getHoldingTime(const time_t &now) const {return now - m_openTime;}
    virtual int getTransDuration() const {return m_closeTime - m_openTime;}
public:
    virtual void initWindowByHistory(WinDiffDataType &&winDiff);
    virtual void updateWindowBySnap(DiffData &diffData, std::ostream *pOut = nullptr);
    int getHalfLifeBars() const { return int(hl_bars_0) +1; }
    std::string getWinDiffDataFields() const {std::ostringstream out; m_winDiff.begin()->outFieldsNames(out); return out.str(); }
    std::ostream & outWinDiffDataValues(std::ostream & out);

public:
    float m_slope,m_intercept ,m_mean, m_std,  m_p,m_pmin;
    int coint_days;
    float std_rate, interval_secs, he_0, hl_bars_0;
    time_t m_start,m_end;

    float m_he {1.0};
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
    time_t  m_openTime {0};
    time_t  m_closeTime {0};
    std::string m_name;
    std::string m_slopeName;
    float m_rank {-1.};
    WinDiffDataType m_winDiff;
    int m_cntWinDiff {0};
};

