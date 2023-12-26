all:|b
	cd b && cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..
	make -C b

#FYI  v_subcmds.h
run:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade test_log --conf  conf/v-trade.json --host 172.22.192.1 --port 7497 --preload_symbols  topV100_MC200
news:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade v_news --conf  conf/v-trade.json --host 172.22.192.1 --port 7497  --preload_symbols  topV100_MC200
scanner:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade v_scanner --conf  conf/v-trade.json --host 172.22.192.1 --port 7497

b:
	mkdir $@
clean:
	rm -fr b


3rd-party: 3rd-party.mk
	make  -f $<
