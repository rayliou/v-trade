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
    float getProfit () const { return m_profit;}
    void addProfit (float value) { m_profit += value;}
    void clearProfit () { m_profit  =0; }
private:
    float m_profit {0};
};

