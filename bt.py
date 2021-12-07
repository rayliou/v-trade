#!/usr/bin/env python3
# coding=utf-8
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import matplotlib.pyplot as plt
import backtrader as bt
import backtrader.feeds as btfeeds
from backtrader.feeds.pandafeed import PandasData
import pandas as pd
import argparse,sys
from History import HistoryYahoo,HistoryFutu

'''
- https://www.backtrader.com/docu/quickstart/quickstart/

'''

class SimpleMovingAverage(bt.Indicator):
    lines = ('sma',)
    params = dict(period=5)

    def __init__(self):
        ...  # Not relevant for the explanation

    def prenext(self):
        print('prenext:: current period:', len(self))

    def nextstart(self):
        print('nextstart:: current period:', len(self))
        # emulate default behavior ... call next
        self.next()

    def next(self):
        print('next:: current period:', len(self))

nCallInit, nCallNext  = 0, 0
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('printlog', False),
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        global nCallInit
        nCallInit +=1
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        # self.sma = bt.indicators.SimpleMovingAverage(
        self.sma = SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)
        self.sma15 = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=15)
        '''
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25,
                                            subplot=True)
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)
        '''

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
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

    def next(self):
        global nCallNext
        nCallNext +=1
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0] and self.sma[0] > self.sma15[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        elif self.dataclose[0] < self.sma[0] and self.sma[0] < self.sma15[0]:

            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' %
                 (self.params.maperiod, self.broker.getvalue()), doprint=True)
    pass



if __name__ == '__main__':
    code = sys.argv[1] if len(sys.argv)> 1 else 'SPY'
    isHK = code.startswith('HK.')
    cerebro = bt.Cerebro()
    # cerebro.addstrategy(bt.Strategy)
    # cerebro.addstrategy(TestStrategy)
    strats = cerebro.optstrategy(
        TestStrategy,
        maperiod=range(3, 4))

    cerebro.broker.setcash(200000.0)
    history = HistoryYahoo()
    history.getKLineOnline(code,30,'1d')
    cerebro.adddata(PandasData(dataname=history.df_))

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # Set the commission
    cerebro.broker.setcommission(commission=0.0)
    # Run over everything
    cerebro.run(maxcpus=1)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print(f'Call init :{nCallInit}; call next {nCallNext}')
    #cerebro.plot(style='bar')

