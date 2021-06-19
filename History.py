#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
import talib
import yfinance as yf
import numpy as np



'''
- HK https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
- US https://github.com/ranaroussi/yfinance/
'''

class History:
    def __init__(self):
        pass
    def priceLine(self):
        t =yf.Ticker("LI")
        t =yf.Ticker("GOOG")
        h = t.history(period="5d", interval='1m', )
        display(h)
        p= (h.High + h.Low + h.Open + h.Close)/4
        pLog = np.log(h.Volume +1)
        #pLog = p * pLog.round(2).hist()
        #p = p.round(2).groupby(axis=1)
        #p = p.round(2).value_counts()
        p = p.round(3).hist(bins=100,figsize = (15,7))
        display(p)
        #display(pLog)


        pass
    def atr(self):
        #self.ctx_ = OpenUSTradeContext(host='127.0.0.1', port=11111, is_encrypt=None, security_firm=SecurityFirm.FUTUSECURITIES)
        t =yf.Ticker("EDU")
        t =yf.Ticker("PG")
        t =yf.Ticker("BEKE")
        t =yf.Ticker("QCOM")
        t =yf.Ticker("INTC")
        t =yf.Ticker("ABNB")
        t =yf.Ticker("TSLA")
        t =yf.Ticker("LI")
        hist = t.history(period="max").tail(100)
        #display(hist.tail(30))
        timeperiod = 14
        atr = talib.ATR(hist.High,hist.Low,hist.Close,timeperiod=timeperiod).tail(30)
        ma = talib.SMA(hist.Close,timeperiod=timeperiod).tail(30)
        ema = talib.EMA(hist.Close,timeperiod=timeperiod).tail(30)
        #display(atr/ma*100)
        #display(ma)
        print('ema------------------')
        display(ema)
        print('atr/ma------------------')
        display(100*atr/ma)
        print('ATR:-------------------')
        display(atr)
        pass
    pass

if __name__ == '__main__':
    h = History()
    h.priceLine()
