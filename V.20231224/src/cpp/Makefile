all:|b
	cd b && cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..
	make -C b
run:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade test_log --conf  conf/v-trade.json --host 172.22.192.1 --port 7497

b:
	mkdir $@
clean:
	rm -fr b


3rd-party: 3rd-party.mk
	make  -f $<
