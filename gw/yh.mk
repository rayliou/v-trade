GROUP=cn
GROUP=topV100_MC200
DATE=$(shell date +%Y%m%d)
FEED_SOURCE=Yahoo

DATA_ROOT=../data_test
UNI_NAME=$(DATE).$(GROUP).$(FEED_SOURCE).test
BIG_TABLE_FILE=$(DATA_ROOT)/bigtable-$(UNI_NAME)_v1.csv
all: $(BIG_TABLE_FILE)
	echo $(GROUP)
$(BIG_TABLE_FILE): $(DATA_ROOT)/start.done
	./GwYahoo.py mdownload  $(GROUP) $@ --interval 5m
	#echo $(DATA_ROOT)
rmtz:
	echo $@
start $(DATA_ROOT)/start.done: 
	mkdir -p $(DATA_ROOT)
	touch $(DATA_ROOT)/start.done
clean:
	rm -fr $(BIG_TABLE_FILE)

.PHONY : start clean
