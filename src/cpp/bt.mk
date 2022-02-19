include global.mk

%.5s.csv:
	./main_lv history --output $@ --dt $* --barSizeSetting "5 secs" --whatToShow "TRADES" --useRTH 1 --formatDate 1 --sym_source conf --conf ../conf/v-trade.json --timeout 600
	#echo $(RUN_DIR)/main_lv history -o $@ --dt $* --barSizeSetting "5 secs" --whatToShow "TRADES,BID_ASK" --useRTH 1 --formatDate 1 --sym_source model --timeout 600


-include history_daily_deps.mk
