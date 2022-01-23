include ../../../vars.mk

BASE_DATE=$(shell python -c  'from datetime import datetime,timedelta; tm = datetime.now()  ; tm -= timedelta(days=tm.weekday()); print(tm.strftime("%Y%m%d"))')
DIFF_DAYS=$(shell python -c  'from datetime import datetime,timedelta; tm = datetime.now() ;  print(1+tm.weekday())')
BIG_TABLE_BASE_FILE=$(DATA_ROOT)/stk-base-$(BASE_DATE).$(GROUP).$(FEED_SOURCE).csv
BIG_TABLE_DAILY_FILE=$(DATA_ROOT)/stk-daily-$(DATE).$(GROUP).$(FEED_SOURCE).csv
BIG_TABLE_DAILY_FILE_1m=$(DATA_ROOT)/stk-daily-$(DATE).$(GROUP).$(FEED_SOURCE).1m.csv
BIG_TABLE_DAILY_FILE_30s=$(DATA_ROOT)/stk-daily-$(DATE).$(GROUP).$(FEED_SOURCE).30s.csv

all:
	GROUP=cn            make -e merge
	GROUP=topV100_MC200 make -e merge
clean:
	GROUP=cn            make -e _clean_daily
	GROUP=topV100_MC200 make -e _clean_daily
clean_all:
	GROUP=cn            make -e _clean
	GROUP=topV100_MC200 make -e _clean

study:
	#GROUP=cn            make -e 1m
	#GROUP=topV100_MC200 make -e 1m
	GROUP=cn            make -e 30s
	GROUP=topV100_MC200 make -e 30s

merge: $(BIG_TABLE_MERGED_FILE)
	echo merge $^  to  $@
$(BIG_TABLE_MERGED_FILE): $(BIG_TABLE_BASE_FILE) $(BIG_TABLE_DAILY_FILE)
	./GwIB.py  merge-df $^ $@
$(BIG_TABLE_DAILY_FILE):
	./GwIB.py  downloadhistory $(GROUP) $@  --interval '5 mins'  --duration '$(DIFF_DAYS) D'  --timeout 600 --conf $(CONF_FILE)

1m: $(BIG_TABLE_DAILY_FILE_1m)
$(BIG_TABLE_DAILY_FILE_1m):
	./GwIB.py  downloadhistory $(GROUP) $@  --interval '1 min'  --duration '20 D'  --timeout 1200 --conf $(CONF_FILE)

30s: $(BIG_TABLE_DAILY_FILE_30s)
$(BIG_TABLE_DAILY_FILE_30s):
	./GwIB.py  downloadhistory $(GROUP) $@  --interval '30 secs'  --duration '30 D'  --timeout 2400 --conf $(CONF_FILE)

$(BIG_TABLE_BASE_FILE): $(DATA_ROOT)/start.done
	#./GwIB.py  downloadhistory $(GROUP) $@  --interval '5 mins' --duration '2 M' --timeout 1200
	./GwYahoo.py mdownload  $(GROUP) $@ --interval 5m --conf $(CONF_FILE)
	#echo $(DATA_ROOT)
rmtz:
	echo $@
start $(DATA_ROOT)/start.done:
	mkdir -p $(DATA_ROOT)
	touch $(DATA_ROOT)/start.done
_clean:
	rm -fr $(BIG_TABLE_BASE_FILE) $(BIG_TABLE_DAILY_FILE) $(BIG_TABLE_MERGED_FILE)
_clean_daily:
	rm -fr $(BIG_TABLE_DAILY_FILE) $(BIG_TABLE_MERGED_FILE)

show:
	@echo Base: $(BIG_TABLE_BASE_FILE)
	@echo daily: $(BIG_TABLE_DAILY_FILE)
	@echo merged: $(BIG_TABLE_MERGED_FILE)
.PHONY : start clean _clean all show _clean_daily clean_all test
