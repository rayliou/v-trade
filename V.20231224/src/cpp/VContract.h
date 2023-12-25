#pragma once
#include <memory>
#include <time.h>
#include <string>
#include <any>
#include <map>
// #include "Ohlcv.h"
#include "Contract.h"

class VContract {
public:
    explicit VContract(const char * symbol):symbol_(symbol) {}
public:
    std::unique_ptr<ContractDetails> ibContractDetails_ {nullptr};
    const char * symbol_ {nullptr};

};
using VectorOfPtrVContract=std::vector<std::unique_ptr<VContract>>;
