include vars.mk
# vars.prod.mk  vars.study.mk
include vars.prod_or_study.mk


#DATE=$(shell date +%Y%m%d)
# BIG_TABLE_MERGED_FILE=/Users/henry/stock/v-trade/data/data_study/stk-merged-20220114.cn.Yahoo.csv
#BIG_TABLE_MERGED_FILE=xxxxxxxxxxxxxxxxx
#END_DATES_LIST=$(shell $(PY_PATH)/pairs_trading/studyCointegrate.py date-list-from-bigcsv  --skipdays 28  $(BIG_TABLE_MERGED_FILE) )

all:
	make m_study
study prod:
	cd /Users/henry/stock/env_$@ && make m_study
#	END_DATES_LIST='2022-01-11 2022-01-12 2022-01-13 2022-01-14' make -e m_study
clean:m_clean
#clean:
#	END_DATES_LIST=$(DATE) make -e m_clean

clean_data:
	for g in $(GROUPS); do\
		GROUP=$${g} make -C $(PY_PATH)/gw clean ;\
	done

GROUPS=cn topV100_MC200

m_study:m_bt
	touch $@

m_bt:m_ols
m_ols:m_coint

m_%:
	for d in $(END_DATES_LIST); do  for g in $(GROUPS); do\
		DATE=$${d} GROUP=$${g} make -e $${d}.$${g}/$*; \
	done; done

BT_DATA_SOURCE=/Users/henry/stock/v-trade/data/data_study/stk-daily-20220113.$(GROUP).Yahoo.30s.csv

$(DATE).$(GROUP)/bt:$(DATE).$(GROUP)/ols
	#$(PY_PATH)/pairs_trading/pairs_trading.py m-bt  $(BT_DATA_SOURCE)  `dirname $@`/ols.csv  `dirname $@`/$(DATE).$(GROUP).bt.csv
	$(CPP_PATH)/main_bt --src  $(BT_DATA_SOURCE) --olscsv  `dirname $@`/ols.csv -v 1 --dst  `dirname $@`/$(DATE).$(GROUP).bt.csv  #info #
	touch $@

$(DATE).$(GROUP)/ols:$(DATE).$(GROUP)/coint
	$(PY_PATH)/pairs_trading/pairs_trading.py ols --windowsize 500  $(BIG_TABLE_MERGED_FILE) --end_date $(DATE)  `dirname $@`/coint.csv  `dirname $@`/ols.csv
	touch $@

$(DATE).$(GROUP)/coint:$(BIG_TABLE_MERGED_FILE) $(STOCK_BY_PLATES_FILE) $(DATE).$(GROUP)/start
	$(PY_PATH)/pairs_trading/pairs_trading.py cointegrate --stock_plates_json $(STOCK_BY_PLATES_FILE) --end_date $(DATE) --max_days 30 $(BIG_TABLE_MERGED_FILE)  `dirname $@`/coint.csv
	touch $@

$(DATE).$(GROUP)/start: $(BIG_TABLE_MERGED_FILE)
	mkdir -p `dirname $@`
	ln -sf $^ `dirname $@`/bigcsv.csv
	touch $@

$(DATE).$(GROUP)/clean:
	rm -vrf  `dirname $@`




show:
	echo END_DATES_LIST=$(END_DATES_LIST)
	BIG_TABLE_MERGED_FILE=$(BIG_TABLE_MERGED_FILE) GROUP=cn  make  -C $(PY_PATH)/gw -e show
	GROUP=topV100_MC200 make  -C $(PY_PATH)/gw -e show
web:
	FLASK_APP=WebMain flask run
xstudy:
	cd $(PY_PATH) && /usr/local/bin/jupyter-lab

hedge: $(WORK_DATA_DIR)/ols.done
#hedge: $(WORK_DATA_DIR)/cointegration.done
	echo aaa

watch_pairs:
	$(PY_PATH)/pairs_trading/pairs_trading.py watchpairs ./$(DATE)*/*ols*.csv --conf $(CONF_FILE)


$(STOCK_BY_PLATES_FILE) :
	$(PY_PATH)/screener/ScreenByPlates.py $@



$(BIG_TABLE_MERGED_FILE):
	cd $(PY_PATH)/gw && make

rmtz:$(BIG_TABLE_MERGED_FILE) $(WORK_DATA_DIR)/start.done
	./S.py $(BIG_TABLE_MERGED_FILE) $(TMP_DATA)

git_push:
	git add conf/*.conf *.py *.md  */*.{py,md}  *.mk Makefile #*/*.mk
	git ci  -am  'xxx'
	git push

.PHONY : hedge start clean git_push web watch_pairs
#.PRECIOUS: %.start %.coint %.m_coint %.ols %.m_ols
