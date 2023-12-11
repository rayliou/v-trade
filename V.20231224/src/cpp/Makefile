all:
	make -C b
run:
	SPDLOG_LEVEL=info,v-main=trace b/v-trade test_log --conf  conf/v-trade.json


3rd-party: 3rd-party.mk
	make  -f $<
