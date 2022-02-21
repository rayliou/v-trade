include global.mk

all:20220126/done
	echo all done

%/done:
	./main_lv history --out_dir $* --dt_to $* --dt_from  20211210 --barSizeSetting "5 secs" --whatToShow "TRADES" --useRTH 1 --formatDate 1 --sym_source conf --conf ../conf/v-trade.json --timeout 600
	touch $@

%.5s.csv:
	./main_lv history --out_dir $* --dt_to $* --dt_from  20211210 --barSizeSetting "5 secs" --whatToShow "TRADES" --useRTH 1 --formatDate 1 --sym_source conf --conf ../conf/v-trade.json --timeout 600

history_daily_deps.mk:
	 ./main_lv history_daily_deps --output $@  --dt_to 20220126 --dt_from  20211210

#-include history_daily_deps.mk
