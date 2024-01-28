
RUN_DIR=./b

bt:xbuild
	cd $(RUN_DIR) && ln -sf ../*.mk .
	make -C $(RUN_DIR)  -f bt.mk

t: $(RUN_DIR)/history_daily_deps.mk
	echo $@

t1:xbuild
	 $(RUN_DIR)/main_lv history_daily_deps --dt_to 20220126 --dt_from  20211210 2>/dev/null
	 #./b/main_lv live --conf  ./conf/v-trade.json
	 #./b/main_lv --conf  ./conf/v-trade.json
$(RUN_DIR)/history_daily_deps.mk:xbuild
	 $(RUN_DIR)/main_lv history_daily_deps --dt_to 20220126 --dt_from  20211210 > $@
xbuild:b
	make -C $(RUN_DIR)
	#touch $@
b:
	mkdir $(RUN_DIR)
	cd $(RUN_DIR) && cmake ..

clean:
	rm -fr $(RUN_DIR)
	rm -vfr *.gch *.pch *.o main_bt main_lv *.d
.PHONY:clean
