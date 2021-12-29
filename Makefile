GROUP=topV100
GROUP=cn
DATE=$(shell date +%Y%m%d)
ROOT=$(DATE).$(GROUP).test
SRC_DATA=data_test/bigtable-Yahoo-20211227-2058_v2.csv
SRC_DATA=data_test/bigtable-20211228.topV100_MC200.Yahoo.test_v1.csv
SRC_DATA=data/20211228.cn.Yahoo.test_bigtable_v1.csv
#SRC_DATA=data_test/bigtable-ib-20211227.csv
TMP_DATA=$(ROOT)/`basename $(SRC_DATA)`
all: hedge
	#echo $(ROOT)
	#echo $(HOME) `pwd`
	#echo $(DATE)

hedge: $(ROOT)/lineregress.done
	echo aaa

lineregress $(ROOT)/lineregress.done:$(ROOT)/cointegration.done
	./Hedge.py lr  $(SRC_DATA) -l $(ROOT)/lineregress.2mon.500bar.csv -w 500 -p $(ROOT)/cointegration.2mon.csv
	./Hedge.py lr  $(SRC_DATA) -l $(ROOT)/lineregress.2mon.800bar.csv -w 800 -p $(ROOT)/cointegration.2mon.csv
	./Hedge.py lr  $(SRC_DATA) -l $(ROOT)/lineregress.1mon.500bar.csv -w 500 -p $(ROOT)/cointegration.1mon.csv
	./Hedge.py lr  $(SRC_DATA) -l $(ROOT)/lineregress.1mon.800bar.csv -w 800 -p $(ROOT)/cointegration.1mon.csv
	touch $(ROOT)/lineregress.done

cointegration $(ROOT)/cointegration.done: $(ROOT)/start.done $(SRC_DATA)
	./Hedge.py coin  $(SRC_DATA) -p $(ROOT)/cointegration.1mon.csv -c 30
	./Hedge.py coin  $(SRC_DATA) -p  $(ROOT)/cointegration.2mon.csv -c 60
	touch $(ROOT)/cointegration.done


start $(ROOT)/start.done: $(SRC_DATA)
	mkdir -p $(ROOT)
	ln -sf $^ $(ROOT)
	touch $(ROOT)/start.done

rmtz:$(SRC_DATA) $(ROOT)/start.done
	./S.py $(SRC_DATA) $(TMP_DATA)
clean:
	rm -fr $(ROOT)

git_push:
	git add *.py */*.py Makefile */*.mk
	git ci  -am  'xxx'
	git push

.PHONY : hedge start clean git_push
