#include vars.mk

#DATE=$(shell date +%Y%m%d)
# BIG_TABLE_MERGED_FILE=/Users/henry/stock/v-trade/data/data_study/stk-merged-20220114.cn.Yahoo.csv
BIG_TABLE_MERGED_FILE=/Users/henry/stock/v-trade/data/data_test/stk-merged-20220116.$(GROUP).Yahoo.csv
BIG_TABLE_MERGED_FILE_CN=/Users/henry/stock/v-trade/data/data_test/stk-merged-20220116.cn.Yahoo.csv

#BT_DATA_SOURCE=/Users/henry/stock/v-trade/data/data_study/stk-daily-20220113.$(GROUP).Yahoo.30s.csv
END_DATES_LIST=$(shell $(PY_PATH)/pairs_trading/studyCointegrate.py date-list-from-bigcsv  --skipdays 28  $(BIG_TABLE_MERGED_FILE_CN) )
#END_DATES_LIST=$(shell $(PY_PATH)/pairs_trading/studyCointegrate.py date-list-from-bigcsv  --skipdays 28  $(BT_DATA_SOURCE) )
END_DATES_LIST=2021-12-17 2021-12-18 2021-12-21 2021-12-22 2021-12-23 2021-12-24 2021-12-28 2021-12-29 2021-12-30 2021-12-31 2022-01-01 2022-01-04 2022-01-05 2022-01-06 2022-01-07 2022-01-08 2022-01-11 2022-01-12 2022-01-13
#END_DATES_LIST=2021-12-17 2021-12-18 2021-12-21 2021-12-22 2021-12-23 2021-12-24 2021-12-28 2021-12-29 2021-12-30 2021-12-31 
