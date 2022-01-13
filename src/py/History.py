#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
import talib
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta

from DataDownloadFutu import DataDownloadFutu



'''
- HK https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
- US https://github.com/ranaroussi/yfinance/
-    https://aroussi.com/post/python-yahoo-finance
'''

class History:
    def __init__(self):
        self.df_ = pd.DataFrame()
        pass
    def priceLineHistogram_(self, h,l,o,c,v,code):
        p= (h+l+o+c)/4
        pLog = np.log(v)
        fig = plt.figure(figsize = (12,8))
        ax = fig.add_subplot(111)
        ax.set_xlabel(f'{code}:price or index '  )
        ax.set_ylabel('Frequency')
        p = p.round(3).hist(bins=100,ax=ax)
        plt.show()
        pass

    def daysToStartEnd(self, days):
        now = datetime.now()
        start = now - timedelta(days=days)
        start = start.strftime('%Y-%m-%d')
        end = (now +timedelta(days=1)) .strftime('%Y-%m-%d')
        return start,end

    def ohlcv(self,df=None):
        assert False, 'You must implement it in subclass'
        return None

    def getKLineFromCSV(self,code,ktype=None,filePath=None):
        assert False, 'You must implement it in subclass'
        return None
    def getKLineOnline(self,code,
            days = 5,
            interval = '1m',   #data interval (intraday data cannot extend last 60 days) Valid intervals are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            start = None,      # If not using days - Download start date string (YYYY-MM-DD) or datetime.
            end   = None,       # If not using days - Download end date string (YYYY-MM-DD) or datetime.
            auto_adjust = True,
            prepost = False     # Include Pre and Post market data in results? (Default is False)
            #actions: Download stock dividends and stock splits events? (Default is True)
            ):
        self.intv2KType_  = {
                '1m' :KLType.K_1M,
                '5m' :KLType.K_5M,
                '15m' :KLType.K_15M,
                '30m' :KLType.K_30M,
                '60m' :KLType.K_60M,
                '1h' :KLType.K_60M,
                '1d' :KLType.K_DAY,
                '1wk' :KLType.K_WEEK,
                }
        s = ','.join(self.intv2KType_.values())
        assert interval in self.intv2KType_, f'Interval:{interval} is not in {s}'
        pass

    pass

class HistoryYahoo(History):
    def __init__(self):
        super().__init__()
        pass
    def getKLineOnline(self,code,
            days = 5,
            interval = '1m',   #data interval (intraday data cannot extend last 60 days) Valid intervals are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            start = None,      # If not using days - Download start date string (YYYY-MM-DD) or datetime.
            end   = None,       # If not using days - Download end date string (YYYY-MM-DD) or datetime.
            auto_adjust = True,
            prepost = False    # Include Pre and Post market data in results? (Default is False)
            #actions: Download stock dividends and stock splits events? (Default is True)
            ):
        super().getKLineOnline(code,days,interval,start,end,auto_adjust,prepost)
        t =yf.Ticker(code)
        if start is None:
            start ,end = self.daysToStartEnd(days)

        print(f'Call history(start={start},end={end}, interval={interval},auto_adjust={auto_adjust},prepost={prepost})')
        df = t.history(start=start,end=end, interval=interval,auto_adjust=auto_adjust,prepost=prepost)
        self.df_ = df
        return self.ohlcv()

    def ohlcv(self,df=None):
        df  = self.df_ if df is None else df
        o   = df.Open
        h   = df.High
        l   = df.Low
        c   = df.Close
        v   = df.Volume
        return o,h,l,c,v

    def priceLineHistogram(self, code = 'ABNB'):
        o,h,l,c,v = self.getKLineOnline(code,days=59,interval='5m')
        self.priceLineHistogram_(h,l,o,c,v,code)
        pass
    def mdownload(self,tickers,
            days = 5,
            interval = '1m',   #data interval (intraday data cannot extend last 60 days) Valid intervals are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            start = None,      # If not using days - Download start date string (YYYY-MM-DD) or datetime.
            end   = None,       # If not using days - Download end date string (YYYY-MM-DD) or datetime.
            auto_adjust = True,
            prepost = False    # Include Pre and Post market data in results? (Default is False)
            ):
        if start is None:
            start ,end = self.daysToStartEnd(days)
            msg = f''' Call yf.download(
                tickers = {tickers},
                start = {start}, end = {end}, interval = {interval},
                group_by = 'ticker', auto_adjust = {auto_adjust}, prepost = {prepost}, threads = True)
                '''
            print(msg)

        data = yf.download(
                tickers = tickers,
                start = start, end = end, interval = interval,
                group_by = 'ticker', auto_adjust = auto_adjust, prepost = prepost, threads = True)


        #data.to_csv('./SPY_IWM.csv')
        return data
        #display(data)

    pass

class HistoryFutu(History):
    def __init__(self):
        super().__init__()
        self.d_ = DataDownloadFutu()
        pass

    def getKLineFromCSV(self,code,ktype=None,filePath=None):
        self.df_ = self.d_.readKLineFromCsv(code,ktype)
        return df

    def getKLineOnline(self,code,
            days = 5,
            interval = '1m',   #data interval (intraday data cannot extend last 60 days) Valid intervals are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            start = None,      # If not using days - Download start date string (YYYY-MM-DD) or datetime.
            end   = None,       # If not using days - Download end date string (YYYY-MM-DD) or datetime.
            auto_adjust = True,
            prepost = False     # Include Pre and Post market data in results? (Default is False)
            #actions: Download stock dividends and stock splits events? (Default is True)
            ):
        super().getKLineOnline(code,days,interval,start,end,auto_adjust,prepost)
        self.df_ = self.d_. getKLine(code,ktype=self.intv2KType_[interval], days=days)
        return self.ohlcv()
    def ohlcv(self,df=None):
        df  = self.df_ if df is None else df
        return self.d_.ohlcv(df)

    def priceLineFutuCSV(self, filePath):
        pass

    def priceLineHistogram(self, code = 'HK.01211'):
        d  = self.d_
        num = int(5.5 * 30 * 10)
        df  = d.getKLine(code,KLType.K_1M,50).tail(num)
        h   = df.high
        l   = df.low
        o   = df.open
        c   = df.close
        v   = df.volume
        self.priceLineHistogram_(h,l,o,c,v,code)
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
    code = sys.argv[1] if len(sys.argv)> 1 else 'SPY'
    isHK = code.startswith('HK.')
    h = HistoryFutu() if isHK else HistoryYahoo()
    #h.mdownload(code, days=729, interval='1h');sys.exit(0)
    h.priceLineHistogram(code);sys.exit(0)
    #r = h.getKLineOnline('ABNB',59,interval = '5m', prepost=True)[0]
    r = h.getKLineOnline('HK.01211',729,interval = '1h')
    display(r)
    sys.exit(0)
    h = HistoryYahoo()
    #r = h.getKLineOnline('ABNB',59,interval = '5m', prepost=True)[0]
    r = h.getKLineOnline('SPY',729,interval = '1h')
    #h.priceLineFutu()
    #h.priceLineYahoo('TSLA')
    #h.priceLineYahoo('ABNB')
    #h.priceLineYahoo('^VIX')
    #h.priceLineFutuCSV('b.data/HK.01211.K1M.csv')
    #plt.show()
    #h.download()
    sys.exit(0)
