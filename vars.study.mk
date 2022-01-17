#include vars.mk

#DATE=$(shell date +%Y%m%d)
# BIG_TABLE_MERGED_FILE=/Users/henry/stock/v-trade/data/data_study/stk-merged-20220114.cn.Yahoo.csv
BIG_TABLE_MERGED_FILE=/Users/henry/stock/v-trade/data/data_test/stk-merged-20220116.$(GROUP).Yahoo.csv
END_DATES_LIST=$(shell $(PY_PATH)/pairs_trading/studyCointegrate.py date-list-from-bigcsv  --skipdays 28  $(BIG_TABLE_MERGED_FILE) )
END_DATES_LIST=2022-01-11 2022-01-12 2022-01-13 2022-01-14
