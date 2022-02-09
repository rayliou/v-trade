CC=/usr/local/Cellar/gcc/11.2.0_3/bin/gcc-11
GCC=/usr/local/Cellar/gcc/11.2.0_3/bin/gcc-11
GXX=/usr/local/Cellar/gcc/11.2.0_3/bin/g++-11

#CXXFLAGS=-g  -std=c++17  -I3rd-party/spdlog/include
CXXFLAGS=-g  -std=gnu++20 -I/usr/local/Cellar/gcc/11.2.0_3/include  -I3rd-party/spdlog/include
LDFLAGS=-L/usr/local/Cellar/gcc/11.2.0_3/lib -lgsl -lgslcblas

GROUP=topV100_MC200
GROUP=cn

M=/Users/henry/stock/env_study/2022-01-19.$(GROUP)/js_coint.json
#loss

LOG_ENV=SPDLOG_LEVEL=err,RunnerBT=trace,s_0=warn,s_dayslr=debug,bt=info,stdout=trace,ContractPairTrade=info 
LOG_ENV=SPDLOG_LEVEL=err,RunnerBT=trace,s_0=trace,s_dayslr=debug,bt=info,stdout=trace,ContractPairTrade=info 
#OUT_TRACE_DATA=--out_trace_data  ./xxx.csv

M=/Users/henry/stock/env_study/2021-12-21.cn/js_coint_v2.json
INCLUES=--out_trace_data  ./xxx.csv --includes MOMO_DQ
INCLUES=

test:main_bt
	$(LOG_ENV) ./$<  $(OUT_TRACE_DATA) --m_src /Users/henry/stock/env_study/2022-01-19.$(GROUP)/bigcsv.csv:$(M) $(INCLUES)
m:main_bt
	 for f in `ls ~/stock/env_study/*.$(GROUP)/js_coint_v2.json` ; do SPDLOG_LEVEL=err,RunnerBT=err,s_0=err,s_dayslr=err,bt=err,stdout=warn,ContractPairTrade=err ./$<  --m_src /Users/henry/stock/env_study/2022-01-19.$(GROUP)/bigcsv.csv:$${f}; done


main_bt: main_bt.cpp Scenario_v1.cpp ContractPairTrade.cpp
	$(GXX)  -o $@ $(CXXFLAGS) $(LDFLAGS) $^  3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  #$<

Scenario_v1: Scenario_v1.cpp common.h.pch  Scenario_v1.h   contract.h  scenario.h  strategy.h
	$(GXX)  -include  common.h  -o $@ $(CXXFLAGS)  $< #$^


Cointegrate:Cointegrate.cpp
	#g++ -o $@ $(CXXFLAGS)  $< #$^
	g++ -o $@ -g  -std=c++17 Cointegrate.cpp 3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  -lgsl -lgslcblas
xtest:Cointegrate
	./$^  ~/stock/env_study/2022-01-01.$(GROUP)/bigcsv.csv  '2022-1-14 0:0:0'

t:t.o
#common.gch:common.h

%.h.gch:%.h
	$(GXX) $(CXXFLAGS)    $^


#%.h.pch:%.h
# 	#$(GXX) $(CXXFLAGS) -stdlib=libc++ -x c++-header $^ -o $@

main_bt.cpp: Scenario_v1.cpp BigTable.h scenario.h
Scenario_v1.cpp: common.h.gch  Scenario_v1.h   contract.h  scenario.h  strategy.h


clean:
	rm -vfr *.gch *.pch *.o main_bt
g:
	git add *.cpp *.h Makefile
	git ci -am 'xxxxxx'
	git push
.PHONY : clean g



#%.o:%.cpp


