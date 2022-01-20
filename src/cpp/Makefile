
CXXFLAGS=-g  -std=c++17  -I3rd-party/spdlog/include


test:main_bt
	./$< /Users/henry/stock/env_study/2021-12-17.cn/bigcsv.csv /Users/henry/stock/env_study/2021-12-17.cn/ols.csv

main_bt: main_bt.cpp Scenario_v0.cpp
	clang++  -include  common.h  -o $@ $(CXXFLAGS)  $^ #$<

Scenario_v0: Scenario_v0.cpp common.h.pch  Scenario_v0.h   contract.h  scenario.h  strategy.h
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

main_bt.cpp: Scenario_v0.cpp BigTable.h scenario.h
Scenario_v0.cpp: common.h.pch  Scenario_v0.h   contract.h  scenario.h  strategy.h


clean:
	rm -vfr *.pch *.o main_bt
.PHONY : clean



#%.o:%.cpp


