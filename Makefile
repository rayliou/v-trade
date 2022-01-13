include vars.mk

all:
	GROUP=cn make -e hedge
	GROUP=topV100_MC200 make -e hedge

clean:
	GROUP=cn make -e clean_
	GROUP=topV100_MC200 make -e clean_

clean_:
	rm -fr $(WORK_DATA_DIR)

show:
	GROUP=cn cd $(PY_PATH)/gw && make show
	GROUP=topV100_MC200 cd $(PY_PATH)/gw && make show
web:
	FLASK_APP=WebMain flask run

#hedge: $(WORK_DATA_DIR)/lineregress.done
hedge: $(WORK_DATA_DIR)/cointegration.done
	echo aaa

lineregress $(WORK_DATA_DIR)/lineregress.done:$(WORK_DATA_DIR)/cointegration.done
	$(PY_PATH)/Hedge.py lr  $(BIG_TABLE_MERGED_FILE) -l $(WORK_DATA_DIR)/lineregress.1mon.500bar.csv -w 500 -p $(WORK_DATA_DIR)/cointegration.1mon.csv
	$(PY_PATH)/Hedge.py lr  $(BIG_TABLE_MERGED_FILE) -l $(WORK_DATA_DIR)/lineregress.1mon.800bar.csv -w 800 -p $(WORK_DATA_DIR)/cointegration.1mon.csv
	touch $(WORK_DATA_DIR)/lineregress.done

cointegrate $(WORK_DATA_DIR)/cointegration.done: $(WORK_DATA_DIR)/start.done $(BIG_TABLE_MERGED_FILE) $(STOCK_BY_PLATES_FILE)
	$(PY_PATH)/pairs_trading/pairs_trading.py cointegrate --stock_plates_json $(STOCK_BY_PLATES_FILE) --max_days 30 $(BIG_TABLE_MERGED_FILE)  $(WORK_DATA_DIR)/cointegration.1mon.csv
	touch $(WORK_DATA_DIR)/cointegration.done
$(STOCK_BY_PLATES_FILE) :
	$(PY_PATH)/screener/ScreenByPlates.py $@


start $(WORK_DATA_DIR)/start.done: $(BIG_TABLE_MERGED_FILE)
	mkdir -p $(WORK_DATA_DIR)
	ln -sf $^ $(WORK_DATA_DIR)
	touch $(WORK_DATA_DIR)/start.done
$(BIG_TABLE_MERGED_FILE):
	cd $(PY_PATH)/gw && make

rmtz:$(BIG_TABLE_MERGED_FILE) $(WORK_DATA_DIR)/start.done
	./S.py $(BIG_TABLE_MERGED_FILE) $(TMP_DATA)

git_push:
	git add *.py *.md  */*.{py,md}  Makefile #*/*.mk
	git ci  -am  'xxx'
	git push

.PHONY : hedge start clean git_push web
