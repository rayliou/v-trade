
t:build
	 ./b/main_lv --conf  ./conf/v-trade.json
build:b
	make -C b
b:
	mkdir b
	cd b && cmake ..
clean:
	rm -fr b
	rm -vfr *.gch *.pch *.o main_bt main_lv *.d
.PHONY:clean
