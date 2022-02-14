GIT_VERSION := $(shell git describe --abbrev=4 --dirty --always --tags)
CXX=/usr/local/Cellar/gcc/11.2.0_3/bin/g++-11
AR=/usr/local/Cellar/gcc/11.2.0_3/bin/gcc-ar-11

IB_LIB_NAME=tws_ib
IB_BASE_DIR=./twsapi_macunix.1014.01_cppclient/client
IB_LIB=$(IB_BASE_DIR)/lib$(IB_LIB_NAME).a


CXXFLAGS=-g  -std=c++20 -DVERSION=$(GIT_VERSION)
CXXFLAGS+= -I/usr/local/Cellar/gcc/11.2.0_3/include  #-I3rd-party/spdlog/include -DVERSION=$(GIT_VERSION)
LDFLAGS=-L/usr/local/Cellar/gcc/11.2.0_3/lib -lgsl -lgslcblas
SRCS=main_lv.o Scenario_v1.o ContractPairTrade.o Backtest.o
OBJS=$(patsubst %, %.o, $(basename $(SRCS)))

main_lv:$(OBJS)
	$(CXX)  -o $@ $(LDFLAGS)  -L$(IB_BASE_DIR) -l$(IB_LIB_NAME)   $^  
main_lv: $(IB_LIB)

$(IB_LIB):
	CXX=$(CXX) AR=$(AR) make -e -C $(IB_BASE_DIR)
#
#用 GCC 和 Makefile 自动处理依赖关系
# http://blog.szm.me/misc/manage_dependencies_with_gcc_and_make/
#
%.o:%.cpp common.h.gch
	$(CXX) $(CXXFLAGS) -c -MT $@ -MMD -MP -MF $*.d -o $@ $<

%.h.gch:%.h
	$(CXX) $(CXXFLAGS)  $^


-include $(patsubst %, %.d, $(basename $(SRCS)))

#CXXFLAGS=-g  -std=c++17  -I3rd-party/spdlog/include

G=cn
G=topV100_MC200

M=/Users/henry/stock/env_study/2022-01-19.$(G)/js_coint.json
#loss

LOG_ENV=SPDLOG_LEVEL=err,RunnerBT=trace,s_0=warn,s_dayslr=debug,bt=info,stdout=trace,ContractPairTrade=info 
LOG_ENV=SPDLOG_LEVEL=err,RunnerBT=trace,s_0=trace,s_dayslr=debug,bt=info,stdout=trace,ContractPairTrade=debug 
LOG_ENV=SPDLOG_LEVEL=err,RunnerBT=trace,s_0=debug,s_dayslr=debug,bt=info,stdout=trace,ContractPairTrade=trace 
#OUT_TRACE_DATA=--out_trace_data  ./xxx.csv

I=--out_trace_data  ./xxx.csv  --includes  INTC_MA
M=/Users/henry/stock/env_study/2022-01-05.cn/js_coint_v2.json
I=--out_trace_data  ./xxx.csv --includes T_V
I=--out_trace_data  ./xxx.csv  --includes PDD_KC


BT:main_bt
	echo $(GIT_VERSION) && exit 0;
	./main_bt
	#find  ~/stock/env_study -name  'js_coint_v2.json'  | SPDLOG_LEVEL=err,Backtest=trace ./main_bt
test:main_bt
	$(LOG_ENV) ./$<  $(OUT_TRACE_DATA) --m_src /Users/henry/stock/env_study/2022-01-19.$(G)/bigcsv.csv:$(M) $(I)
m:main_bt
	 for f in `ls ~/stock/env_study/*.$(G)/js_coint_v2.json` ; do SPDLOG_LEVEL=err,RunnerBT=err,s_0=err,s_dayslr=err,bt=err,stdout=warn,ContractPairTrade=err ./$<  --m_src /Users/henry/stock/env_study/2022-01-19.$(G)/bigcsv.csv:$${f}; done


main_bt: main_bt.cpp Scenario_v1.cpp ContractPairTrade.cpp Backtest.cpp
	$(GXX)  -o $@ $(CXXFLAGS) $(LDFLAGS) $^  3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  #$<

Scenario_v1: Scenario_v1.cpp common.h.pch  Scenario_v1.h   contract.h  scenario.h  strategy.h
	$(GXX)  -include  common.h  -o $@ $(CXXFLAGS)  $< #$^


Cointegrate:Cointegrate.cpp
	#g++ -o $@ $(CXXFLAGS)  $< #$^
	g++ -o $@ -g  -std=c++17 Cointegrate.cpp 3rd-party/JohansenCointegration/JohansenHelper.cpp -I./3rd-party/JohansenCointegration/  -lgsl -lgslcblas
xtest:Cointegrate
	./$^  ~/stock/env_study/2022-01-01.$(G)/bigcsv.csv  '2022-1-14 0:0:0'

t:t.o
#common.gch:common.h


#%.h.pch:%.h
# 	#$(GXX) $(CXXFLAGS) -stdlib=libc++ -x c++-header $^ -o $@

main_bt.cpp: Scenario_v1.cpp BigTable.h scenario.h
Scenario_v1.cpp: common.h.gch  Scenario_v1.h   contract.h  scenario.h  strategy.h


clean:
	rm -vfr *.gch *.pch *.o main_bt main_lv *.d
g:
	git add *.cpp *.h Makefile
	git ci -am 'xxxxxx'
	git push
.PHONY : clean g



#%.o:%.cpp


