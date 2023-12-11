#pragma once
#include "Ohlcv.h"
#include <iostream>
#include <list>
#include <map>
#include <string>

// Class BigTable, derived from Ohlcv::TimeMapOhlcv, to manage and process OHLCV
// data.
class BigTable : public Ohlcv::TimeMapOhlcv {
  public:
    // Retrieves the column index for a given symbol.
    int getSymbolIndex(const std::string &symbol) const;

    // Logs information about the BigTable object.
    void debug(LogType log);

    // Loads data from a specified file into the BigTable.
    void load(std::string fileName);

    // Overloads the stream insertion operator to output BigTable data.
    friend std::ostream &operator<<(std::ostream &o, BigTable &b);

  private:
    // Helper function to output BigTable data to a stream.
    void dump(std::ostream &os);

    // Stores the list of source file names.
    std::list<std::string> m_sourceList;

    // Maps symbols to their respective column indices.
    using SymbolToColIdx = std::map<std::string, int>;
    SymbolToColIdx m_symbolToColIdx;
};

// Stream insertion operator to output BigTable data.
std::ostream &operator<<(std::ostream &o, BigTable &b);
