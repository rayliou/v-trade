
CXXFLAGS=-g  -std=c++17  -I3rd-party/spdlog/include

Scenario_v0: Scenario_v0.cpp  Scenario_v0.h  common.h  contract.h  scenario.h  strategy.h
	clang++ -o $@ $(CXXFLAGS)  $< #$^

bt: main_bt.cpp BigTable.h  deal.h  scenario.h  strategy.h
	g++ -o $@ $(CXXFLAGS)  $< #$^

Cointegrate:Cointegrate.cpp
	#g++ -o $@ $(CXXFLAGS)  $< #$^
	g++ -o $@ -g  -std=c++17 Cointegrate.cpp 3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  -lgsl -lgslcblas
test:Cointegrate
	./$^  ~/stock/env_study/2022-01-01.cn/bigcsv.csv  '2022-1-14 0:0:0'

t:t.o

#%.o:%.cpp


