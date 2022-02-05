
CXXFLAGS=-g  -std=c++17  -I3rd-party/spdlog/include

GROUP=cn
GROUP=topV100_MC200

M=/Users/henry/stock/env_study/2022-01-19.$(GROUP)/js_coint.json
#loss

LOG_ENV=SPDLOG_LEVEL=err,RunnerBT=trace,s_0=warn,s_dayslr=debug,bt=info,stdout=trace,ContractPairTrade=info 
M=/Users/henry/stock/env_study/2021-12-16./js_coint.json
M=/Users/henry/stock/env_study/2022-01-05.$(GROUP)/js_coint.json
M=/Users/henry/stock/env_study/2022-01-01.cn/js_coint.json
#OUT_TRACE_DATA=--out_trace_data  ./xxx.csv
INCLUES=
INCLUES=--out_trace_data  ./xxx.csv --includes VIPS_GTEC

test:main_bt
	$(LOG_ENV) ./$<  $(OUT_TRACE_DATA) --m_src /Users/henry/stock/env_study/2022-01-19.$(GROUP)/bigcsv.csv:$(M) $(INCLUES)
m:main_bt
	 for f in `ls ~/stock/env_study/*.$(GROUP)/js_coint.json` ; do SPDLOG_LEVEL=err,RunnerBT=err,s_0=err,s_dayslr=err,bt=err,stdout=warn,ContractPairTrade=err ./$<  --m_src /Users/henry/stock/env_study/2022-01-19.$(GROUP)/bigcsv.csv:$${f}; done


main_bt: main_bt.cpp Scenario_v1.cpp ContractPairTrade.cpp
	clang++  -include  common.h  -o $@ $(CXXFLAGS)  $^  3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  -lgsl -lgslcblas   #$<

Scenario_v1: Scenario_v1.cpp common.h.pch  Scenario_v1.h   contract.h  scenario.h  strategy.h
	clang++  -include  common.h  -o $@ $(CXXFLAGS)  $< #$^


Cointegrate:Cointegrate.cpp
	#g++ -o $@ $(CXXFLAGS)  $< #$^
	g++ -o $@ -g  -std=c++17 Cointegrate.cpp 3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  -lgsl -lgslcblas
xtest:Cointegrate
	./$^  ~/stock/env_study/2022-01-01.$(GROUP)/bigcsv.csv  '2022-1-14 0:0:0'

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


