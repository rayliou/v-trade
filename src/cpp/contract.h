//g++ -g  -std=c++17  ./bigcsv.cpp -o b && ./b
#pragma once

using namespace std;

class Position {
public:
    int   m_position {0};
    float m_avgprice {-1};

};

class IContract{
public:
    virtual ~IContract( ) {}
    virtual string getName() const = 0;
    float getProfit () const { return m_profit;}
    float getTransactionNum () const { return m_transNum;}
    void addProfit (float value) { m_profit += value; m_transNum++;}
    void clearProfit () { m_profit  =0; m_transNum = 0; }
private:
    float m_profit {0};
    int m_transNum {0};
};

