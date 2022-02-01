
CXXFLAGS=-g  -std=c++17  -I3rd-party/spdlog/include


test:main_bt
	#SPDLOG_LEVEL=err,RunnerBT=trace,Scenario_v1=debug,bt=info,stdout=trace ./$<  --m_src /Users/henry/stock/v-trade/data/data_test/stk-daily-20220124.topV100_MC200.Yahoo.1m.csv:/Users/henry/stock/env_study/2021-12-17.cn/ols.csv
	SPDLOG_LEVEL=err,RunnerBT=trace,s_0=debug,s_dayslr=debug,bt=info,stdout=trace,ContractPairTrade=debug ./$<  --m_src /Users/henry/stock/env_study/2022-01-19.cn/bigcsv.csv:/Users/henry/stock/env_study/2022-01-19.cn/js_coint.json #--includes BIDU,JD

main_bt: main_bt.cpp Scenario_v1.cpp ContractPairTrade.cpp
	clang++  -include  common.h  -o $@ $(CXXFLAGS)  $^  3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  -lgsl -lgslcblas   #$<

Scenario_v1: Scenario_v1.cpp common.h.pch  Scenario_v1.h   contract.h  scenario.h  strategy.h
	clang++  -include  common.h  -o $@ $(CXXFLAGS)  $< #$^


Cointegrate:Cointegrate.cpp
	#g++ -o $@ $(CXXFLAGS)  $< #$^
	g++ -o $@ -g  -std=c++17 Cointegrate.cpp 3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  -lgsl -lgslcblas
xtest:Cointegrate
	./$^  ~/stock/env_study/2022-01-01.cn/bigcsv.csv  '2022-1-14 0:0:0'

t:t.o

%.h.pch:%.h
	clang++ $(CXXFLAGS) -stdlib=libc++ -x c++-header $^ -o $@
	#clang++ $(CXXFLAGS) -cc1 $^ -emit-pch -o $@

main_bt.cpp: Scenario_v1.cpp BigTable.h scenario.h
Scenario_v1.cpp: common.h.pch  Scenario_v1.h   contract.h  scenario.h  strategy.h


clean:
	rm -vfr *.pch *.o main_bt
.PHONY : clean



#%.o:%.cpp


