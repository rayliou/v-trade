SERVER_IP=172.19.128.1
SERVER_PORT?=4001
SERVER_PORT?=7496

all:|b
	cd b && cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..
	make -C b -j 12

#FYI  v_subcmds.h
run:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade test_log --conf  conf/v-trade.json --host $(SERVER_IP) --port $(SERVER_PORT) --preload_symbols  topV100_MC200
history:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade v_tws_history --conf  conf/v-trade.json --host $(SERVER_IP) --port $(SERVER_PORT)  --preload_symbols  topV100_MC200
events:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade v_tws_events --conf  conf/v-trade.json --host $(SERVER_IP) --port $(SERVER_PORT)  --preload_symbols  topV100_MC200
news:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade v_news --conf  conf/v-trade.json --host $(SERVER_IP) --port $(SERVER_PORT)  --preload_symbols  topV100_MC200
scanner:
	SPDLOG_LEVEL=trace,v-main=trace b/v-trade v_scanner --conf  conf/v-trade.json --host $(SERVER_IP) --port $(SERVER_PORT)

b:
	mkdir $@
clean:
	rm -fr b


3rd-party: 3rd-party.mk
	make  -f $<
