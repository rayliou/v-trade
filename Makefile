
GROUP='cn|topV100_MC200'
DATE=$(shell date +%Y%m%d)
FEED_SOURCE=Yahoo

DATA_ROOT=./data_test
UNI_NAME=$(DATE).$(GROUP).$(FEED_SOURCE).test
BIG_TABLE_FILE=$(DATA_ROOT)/bigtable-$(UNI_NAME)_v1.csv

ROOT=./$(UNI_NAME)
#BIG_TABLE_FILE=data_test/bigtable-Yahoo-20211227-2058_v2.csv
#BIG_TABLE_FILE=data_test/bigtable-20211228.topV100_MC200.Yahoo.test_v1.csv
#BIG_TABLE_FILE=data/20211228.cn.Yahoo.test_bigtable_v1.csv
#BIG_TABLE_FILE=data_test/bigtable-ib-20211227.csv
TMP_DATA=$(ROOT)/`basename $(BIG_TABLE_FILE)`
all: hedge
	#echo $(ROOT)
	#echo $(HOME) `pwd`
	#echo $(DATE)

hedge: $(ROOT)/lineregress.done
	echo aaa

lineregress $(ROOT)/lineregress.done:$(ROOT)/cointegration.done
	./Hedge.py lr  $(BIG_TABLE_FILE) -l $(ROOT)/lineregress.2mon.500bar.csv -w 500 -p $(ROOT)/cointegration.2mon.csv
	./Hedge.py lr  $(BIG_TABLE_FILE) -l $(ROOT)/lineregress.2mon.800bar.csv -w 800 -p $(ROOT)/cointegration.2mon.csv
	./Hedge.py lr  $(BIG_TABLE_FILE) -l $(ROOT)/lineregress.1mon.500bar.csv -w 500 -p $(ROOT)/cointegration.1mon.csv
	./Hedge.py lr  $(BIG_TABLE_FILE) -l $(ROOT)/lineregress.1mon.800bar.csv -w 800 -p $(ROOT)/cointegration.1mon.csv
	touch $(ROOT)/lineregress.done

cointegration $(ROOT)/cointegration.done: $(ROOT)/start.done $(BIG_TABLE_FILE)
	./Hedge.py coin  $(BIG_TABLE_FILE) -p $(ROOT)/cointegration.1mon.csv -c 30
	./Hedge.py coin  $(BIG_TABLE_FILE) -p  $(ROOT)/cointegration.2mon.csv -c 60
	touch $(ROOT)/cointegration.done


start $(ROOT)/start.done: $(BIG_TABLE_FILE)
	mkdir -p $(ROOT)
	ln -sf $^ $(ROOT)
	touch $(ROOT)/start.done

rmtz:$(BIG_TABLE_FILE) $(ROOT)/start.done
	./S.py $(BIG_TABLE_FILE) $(TMP_DATA)
clean:
	rm -fr $(ROOT)

git_push:
	git add *.py */*.py Makefile */*.mk
	git ci  -am  'xxx'
	git push

.PHONY : hedge start clean git_push
