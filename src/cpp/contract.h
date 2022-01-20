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
public:
    float m_profit {0};
};

