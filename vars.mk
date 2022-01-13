
GROUP='cn|topV100_MC200'
DATE=$(shell date +%Y%m%d)
FEED_SOURCE=Yahoo

ROOT=/Users/henry/stock/v-trade
PY_PATH=$(ROOT)/src/py

DATA_STATIC=$(ROOT)/data/data_static
STOCK_BY_PLATES_FILE=$(DATA_STATIC)/ScreenByPlates-20220112.json
DATA_ROOT=$(ROOT)/data/data_test
UNI_NAME=$(DATE).$(GROUP).$(FEED_SOURCE).test
BIG_TABLE_MERGED_FILE=$(DATA_ROOT)/stk-merged-$(DATE).$(GROUP).$(FEED_SOURCE).csv

CONF_FILE=$(ROOT)/conf/v-trade.utest.conf


WORK_DATA_DIR=./$(UNI_NAME)
#BIG_TABLE_MERGED_FILE=data_test/bigtable-Yahoo-20211227-2058_v2.csv
#BIG_TABLE_MERGED_FILE=data_test/bigtable-20211228.topV100_MC200.Yahoo.test_v1.csv
#BIG_TABLE_MERGED_FILE=data/20211228.cn.Yahoo.test_bigtable_v1.csv
#BIG_TABLE_MERGED_FILE=data_test/bigtable-ib-20211227.csv
TMP_DATA=$(WORK_DATA_DIR)/`basename $(BIG_TABLE_MERGED_FILE)`
