#!/usr/bin/env python3

##########################
# https://ca.finance.yahoo.com/quote/AAPL/history?p=AAPL
from datetime import datetime
import backtrader as bt
from condition import Condition
from pprint import pprint

# Create a subclass of Strategy to define the indicators and logic

class VWAP(bt.Indicator):
    lines = ('vwap',)
    params = (('period', 30),)

    def __init__(self):
        self.addminperiod(self.params.period)
        self.cumulative_total = bt.ind.SumN(self.data.volume * self.data.close, period=self.params.period)
        self.cumulative_volume = bt.ind.SumN(self.data.volume, period=self.params.period)

    def next(self):
        self.lines.vwap[0] = self.cumulative_total[0] / self.cumulative_volume[0] if self.cumulative_volume[0] else float('nan')



class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict( pfast=10, pslow=20 )
    params = dict( pfast=5, pslow=20 )

    def __init__(self):
        self.cnt_ = 0
        self.last_high_ = 0
        ema1 = bt.ind.EMA(period=self.p.pfast)  # fast moving average
        ema2 = bt.ind.EMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(ema1, ema2)  # crossover signal
        self.dataclose = self.datas[0].close
        ema200 = bt.ind.EMA(period=200)
        self.v1_ = ema200
        self.v2_ = bt.ind.EMA(period=100)
        self.v3_ = bt.ind.EMA(period=50)
        self.v4_ = bt.ind.EMA(period=20)
        self.v5_ = bt.ind.EMA(period=10)
        self.v6_ = bt.ind.EMA(period=5)
        self.c_  = Condition()
        self.atr5_ = bt.ind.ATR(period=5)
        self.atr20_ = bt.ind.ATR(period=20)
        self.ema_vol_short_ = bt.ind.EMA(self.data.volume, period=5)
        self.ema_vol_long_  = bt.ind.EMA(self.data.volume, period=20)
        self.vwap_ = VWAP()
        self.last_value_ = 0

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def xxxx_log(self):
        dt = self.datas[0].datetime.date(0).isoformat()
        atr5 = "{:.2f}".format(self.atr5_[0])
        atr20 = "{:.2f}".format(self.atr20_[0])
        vwap = "{:.2f}".format(self.vwap_[0])
        ema_vol_ratio = "{:.2f}".format(self.ema_vol_short_[0] / self.ema_vol_long_[0])
        print(f"[{dt}] ATR5: {atr5:6}, ATR20: {atr20:6}, VWAP: {vwap:6}, Vol_EMA 2/20 Ratio: {ema_vol_ratio:6}")
        v0  = self.dataclose[0]
        v1  = self.v1_[0]
        v2  = self.v2_[0]
        v3  = self.v3_[0]
        v4  = self.v4_[0]
        v5  = self.v5_[0]
        v6  = self.v6_[0]
        self.c_.update_values(v0, v1,v2,v3,v4,v5,v6)
    def next(self):
        self.cnt_ += 1
        # possize = self.getposition(self.data, self.broker).size
        # print(possize)
        cash = self.broker.get_cash()  # 获取当前现金余额
        price = self.dataclose[0]  # 获取当前股票价格
        dt = self.datas[0].datetime.date(0).isoformat()
        if self.dataclose[0] > self.last_high_:
            self.last_high_  = self.dataclose[0]
        ema_vol_ratio = self.ema_vol_short_[0] / self.ema_vol_long_[0]
        # print(self.position)
        if not self.position :  # not in the market
            if self.crossover > 0 \
                and self.dataclose[0] >  self.v1_[0] \
                and self.v2_[1] > self.v1_[0]:
            # if self.dataclose[0] / self.dataclose[-1] > 1.03 and ema_vol_ratio > 1.5:  # if fast crosses slow to the upside
                size = int(cash / price) - 30
                if size > 0:
                    self.order_target_size(target=size)
                    self.last_value_ = self.broker.get_value()
        elif (self.dataclose[0] + 2.8 *self.atr5_ < self.last_high_ and ema_vol_ratio > 1.8) \
          or self.dataclose[0] + 6.8 *self.atr20_ < self.last_high_:
        # elif self.dataclose[0] + 1.8 *self.atr5_ < self.last_high_:
            self.order_target_size(target=0)  # close long position
            gain_perc =  (self.broker.get_value() - self.last_value_ )/self.last_value_  *100
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.last_high_  = order.executed.price
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.last_high_  = 0
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))


    def stop(self):
        # pprint(self.c_.state_2_cnt_)
        # print(f"Size of state:{len(self.c_.state_2_cnt_)}")
        # pprint(self.c_.state_change_2_cnt_)
        print(f"Size of state_change dict:{len(self.c_.state_change_2_cnt_)}")
        cash = self.broker.get_cash()
        value = self.broker.get_value()
        print(f"Cash:{cash}, value:{value}")

        pass


cerebro = bt.Cerebro()  # create a "Cerebro" engine instance

cerebro.broker.set_cash(100000)
cerebro.broker.setcommission(commission=0.001)


# Create a data feed
#data = bt.feeds.YahooFinanceData(dataname='MSFT',
csv_file = "AAPL.csv"
csv_file = "SPY.csv"
csv_file = "QQQ.csv"
# data = bt.feeds.YahooFinanceCSVData(dataname=csv_file, fromdate=datetime(1999, 1, 1))
# data = bt.feeds.YahooFinanceCSVData(dataname=csv_file, fromdate=datetime(1999, 1, 1), todate=datetime(2023, 12, 31))
# data = bt.feeds.YahooFinanceCSVData(dataname=csv_file, fromdate=datetime(2000, 1, 1), todate=datetime(2023, 12, 31))
# data = bt.feeds.YahooFinanceCSVData(dataname=csv_file, fromdate=datetime(2000, 1, 1), todate=datetime(2010, 12, 31))
# data = bt.feeds.YahooFinanceCSVData(dataname=csv_file, fromdate=datetime(2021, 1, 1), todate=datetime(2023, 12, 31))
# data = bt.feeds.YahooFinanceCSVData(dataname=csv_file, fromdate=datetime(2010, 1, 1), todate=datetime(2023, 12, 31))
data = bt.feeds.YahooFinanceCSVData(dataname=csv_file, fromdate=datetime(2008, 1, 1))

cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.01)
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')



cerebro.adddata(data)  # Add the data feed

cerebro.addstrategy(SmaCross)  # Add the trading strategy
# print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
start_cash = cerebro.broker.getvalue()
results = cerebro.run()  # run it all
first_strategy = results[0]

# sharpe_ratio = first_strategy.analyzers.sharpe.get_analysis()
# max_drawdown = first_strategy.analyzers.drawdown.get_analysis()
# returns = first_strategy.analyzers.returns.get_analysis()
# trade_analysis = first_strategy.analyzers.trade_analyzer.get_analysis()

# # 格式化输出
# formatted_sharpe_ratio = format_analysis(sharpe_ratio)
# formatted_max_drawdown = format_analysis(max_drawdown)
# formatted_returns = format_analysis(returns)
# formatted_trade_analysis = format_analysis(trade_analysis)

# print(f"夏普率: {formatted_sharpe_ratio}")
# print(f"最大回撤: {formatted_max_drawdown}")
# print(f"平均收益: {formatted_returns}")
# print(f"交易分析: {formatted_trade_analysis}")

rnorm100 = first_strategy.analyzers.returns.get_analysis()['rnorm100']
max_drawdown = first_strategy.analyzers.drawdown.get_analysis()["max"]

# print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
end_cash = cerebro.broker.getvalue()
return_rate  = (end_cash - start_cash)/start_cash * 100
print(f"Return rate :{return_rate:.3f}% and anual return rate: {rnorm100:.3f}% Max Drawdown(len:{max_drawdown['len']}, max_drawdown:{max_drawdown['drawdown']:.3f}%) ")
cerebro.plot()  # and plot it with a single command
