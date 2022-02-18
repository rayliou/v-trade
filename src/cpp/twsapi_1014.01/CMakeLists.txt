cmake_minimum_required(VERSION 3.10)

# set the project name
project(tws_ib)
find_library(BID bid lib)

# add the executable
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

add_library(tws_ib ${BID} ContractCondition.cpp DefaultEWrapper.cpp EClient.cpp EClientSocket.cpp EDecoder.cpp EMessage.cpp EMutex.cpp EOrderDecoder.cpp EReader.cpp EReaderOSSignal.cpp ESocket.cpp MarginCondition.cpp OperatorCondition.cpp OrderCondition.cpp PercentChangeCondition.cpp PriceCondition.cpp SoftDollarTier.cpp StdAfx.cpp TimeCondition.cpp VolumeCondition.cpp executioncondition.cpp)
#target_link_libraries(tws_lib $(BID))
