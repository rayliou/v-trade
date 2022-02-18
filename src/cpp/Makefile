
t:xbuild
	 ./b/main_lv live --conf  ./conf/v-trade.json
	 #./b/main_lv history_daily_deps
	 #./b/main_lv --conf  ./conf/v-trade.json
xbuild:b
	make -C b
b:
	mkdir b
	cd b && cmake ..
clean:
	rm -fr b
	rm -vfr *.gch *.pch *.o main_bt main_lv *.d
.PHONY:clean
