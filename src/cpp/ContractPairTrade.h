//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once
#include <any> // std::stringstream
#include <sstream> // std::stringstream
#include <regex>
#include "contract.h"
#include <limits>
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

struct DiffDataBase {
    time_t tm;
    float p1 {0.}, p2 {0.};
    float diff;
};
struct DiffData : public DiffDataBase{
    float avg_diffdiff {0.};
    float mean0 {0.};
    float mean {0.};
    float mean_half {0.};

    float ema {0.};
    float ema_half {0.};
    float ema_quarter {0.};
    float ema_5bars {0.};

    float em_var {0.};
    float em_var_half {0.};
    float em_var_quarter {0.};
    float em_var_5bars {0.};

    float std0 {-1.};
    float std {-1.};
    float sm_std_5 {0.};
    float sm_std_10 {0.};
    float sm_std_20 {0.};
    float diffH {- std::numeric_limits<float>::infinity()  };
    float diffL {std::numeric_limits<float>::infinity() };
    float stdH {- std::numeric_limits<float>::infinity() };
    float stdL {std::numeric_limits<float>::infinity() };
    float z {0.};
    std::ostream & outFieldsNames(std::ostream &out) const {
        out << "std0,std,mean0,mean,mean_half,tm,diff,z";
        out << ",sm_std_5,sm_std_10,sm_std_20";
        out << ",stdH,stdL";
        out << ",diffH,diffL";
        out << ",avg_diffdiff";

        out << ",ema";
        out << ",ema_half";
        out << ",ema_quarter";
        out << ",ema_5bars";
        out << ",em_var";
        out << ",em_var_half";
        out << ",em_var_quarter";
        out << ",em_var_5bars";
        return out;
    }
    std::ostream & outValues(std::ostream &out) const {
        out << std0 << ',' << std << "," << mean0 << ',' << mean << "," << mean_half << "," ;
        out << tm << "," << diff << "," << z;
        out << "," << sm_std_5 << "," << sm_std_10<< "," << sm_std_20;
        out << "," << stdH << "," << stdL;
        out << "," << diffH << "," << diffL;
        out << "," << avg_diffdiff;

        out << "," << ema;
        out << "," << ema_half;
        out << "," << ema_quarter;
        out << "," << ema_5bars;
        out << "," << em_var;
        out << "," << em_var_half;
        out << "," << em_var_quarter;
        out << "," << em_var_5bars;
        return out;
    }
    std::string  toString() const {
        std::ostringstream os;
        outFieldsNames(os);
        os << ":";
        outValues(os);
        return os.str();
    }
    void debug(LogType log, int i, int totalCnt, std::string name = "") {
        auto v = toString();
        log->debug("{}\tdiffData:[{}/{}]:{}", name,i, totalCnt,v);
    }

};
class WinDiffDataType :public std::list<DiffData> {
    //typedef typename std::list<DiffData>      L;
    using L=std::list<DiffData>;
    //typedef typename L::const_iterator        const_iterator;
public:
    int getTickCnt() const { return cntTick;}
    void push_back( DiffData &d, bool incTickCnt) { L::push_back(d); if(incTickCnt) {cntTick++;}}
private:
    int cntTick {0};
};

class ContractPairTrade : public IContract {
public:
    ContractPairTrade (json& j,Money &m, std::string &slopeName);

    //ContractPairTrade (csv::CSVRow& row, Money &m);

    std::vector<std::string>  getSymbols() const;
    time_t getOpenTime() const { return m_openTime;}

    void  setAvailable(bool available) { m_isAvailable = available; }
    bool  isAvailable() { return  m_isAvailable && m_slope != 0.;} 

    void debug(LogType log) ;
    int curPositionDirection() const {
        auto pos =  m_position1.m_position ;
        // pos_x <0 -> n1 is too high, need to be reversed to low
        return pos < 0 ? 1 :(
            pos > 0? -1:0
        );
    }
    void newPosition(int direction, float profitCap,float x, float y);
    void newPosition(float x, float y, bool buyN1,float z0, const time_t &t, const std::map<std::string, std::any> &ext);
    float  closePosition(float x, float y);
    float  closePosition(float x, float y,const time_t &t, const std::map<std::string, std::any> & ext);
    virtual string getName() const { return m_name; }
    virtual void setRank(float rank)  {m_rank = rank;}
    virtual float getRank() const { return m_rank;}
    virtual int getHoldingTime(const time_t &now) const {return now - m_openTime;}
    virtual int getTransDuration() const {return m_closeTime - m_openTime;}
public:
    void addLongDiffItem(DiffDataBase &b);
    virtual void initWindowByHistory(WinDiffDataType &&winDiff);
    void updateLongWindow(DiffData &diffData);
    void updateEMA(DiffData &diffData);
    virtual  WinDiffDataType & updateWindowBySnap(DiffData &diffData, std::ostream *pOut = nullptr);

    float getSpread () const { return m_winDiff.rbegin()->ema_5bars; }
    float getSpreadMean () const { return m_winDiff.rbegin()->ema; }
    float getSpreadStd () const { return std::sqrt(m_winDiff.rbegin()->em_var); }

    time_t getCointegrateStart() const { return m_start ;}
    time_t getCointegrateEnd() const { return m_end ;}
    int getHalfLifeBars() const { return int(hl_bars_0) +1; }
    int getLookBackBars() const {
        return  getHalfLifeBars() *4;
        return (m_end - m_start)/interval_secs /3 ;
        return  1.5 *3600 * 6.5 /interval_secs;  
    }
    int getHalfLifeSecs() const { return halflifeSecs; }
    std::string getWinDiffDataFields() const {std::ostringstream out; m_winDiff.begin()->outFieldsNames(out); return out.str(); }
    std::ostream & outWinDiffDataValues(std::ostream & out);
    float getProfitCap () const { return m_profitCap;}
    float getHurstExponent () const { return he_0;;}
    float getSlopeDiffRate () const { return m_slopeDiffRate;}
    void setMoneyCoeff (float coeff) {m_moneyCoeff = coeff;}

public:
    float m_slope {0.} ,m_intercept ,m_mean, m_std,  m_pxy {-1}  ,m_pyx {-1};
    float m_mean0 {0.}, m_std0 {0.};
    int coint_days;
    float std_rate, interval_secs,  hl_bars_0;
    time_t m_start,m_end;

    float m_z {0};
    float m_zPrev {0};
    float m_z0 {0};
    std::string m_ext, m_n1,m_n2;
    std::pair<std::string, std::string> m_symbolsPair;
    // s,i,m,st,pair,p,pmin,ext
    SnapData * m_snap1;;
    SnapData *  m_snap2;;
    Position m_position1;
    Position m_position2;

    bool m_hasCrossedStd_near {false};
    bool m_hasCrossedStd_far {false};
    bool m_hasCrossedStd_far2 {false};
    bool m_hasCrossedStd_far3 {false};

    bool m_hasCrossedMean {false};
    bool m_hasCrossedMean_half {false};
    float m_diffFarest {0.};
    int m_cntCrsDwn_sm_std_20 {0};
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
    std::list<DiffDataBase> m_longWindowDiff;
    int m_cntWinDiff {0};
    float m_slopeDiffRate {100.};
    float m_profitCap {0.};
    int halflifeSecs {-1};
    float he_0 {1.};
    float  m_moneyCoeff {1};

};

