#!/usr/bin/env python3
# coding=utf-8
#from futu import *
from IPython.display import display, HTML
from pyhocon import ConfigFactory
import os.path,os,sys,time
#import talib
import yfinance as yf
import logging,json
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit
import pandas as pd

'''
- https://www.nasdaq.com/market-activity/stocks/screener

'''


class TickerScreener:
    log = logging.getLogger("main.TickerScreener")
    def __init__(self, confPath='../conf/v-trade.utest.conf'):
        #self.confPath_ = 'conf/v-trade.conf'
        self.confPath_ = confPath
        self.c_ = ConfigFactory.parse_file(self.confPath_)
        self.dataRoot_ =  self.c_ .data.rootDir
        assert self.dataRoot_ is not None and self.dataRoot_ != ''
        #print( self.c_.ticker.stock.us.topV100_MC200)

        pass
    def topNasdaq(self):
        file = '~/Downloads/nasdaq_screener_1641678047202.csv'
        df = pd.read_csv(file)
        df.Symbol = df.Symbol.str.strip()
        # https://pandas.pydata.org/docs/reference/api/pandas.Series.str.replace.html
        df['Last Sale'] = df['Last Sale'].str.replace('$', '' ,regex=False).astype('float')
        df = df[df['Last Sale'] >5]
        df['volume_dollar'] = df['Last Sale']* df.Volume
        #df['Last Sale'].dtype
        df_sorted_by_v   = df.sort_values(by='volume_dollar',ascending=False)
        df_sorted_by_mc  = df.sort_values(by='Market Cap',ascending=False)

        nTopMktCap = 200
        nTopVlm   = 100

        nTopMktCap = 7000
        nTopVlm   = 5000

        nTopMktCap = 400
        nTopVlm   = 300
        setTopMktCap = set(df_sorted_by_mc.head(nTopMktCap).Symbol )
        setTopMktCap
        #display(df_sorted_by_v)
        df_sorted_by_v = df_sorted_by_v.head(nTopVlm)
        df_sorted_by_v = df_sorted_by_v.loc[lambda df: [s in setTopMktCap  for s in df.Symbol] ,:]
        print(df_sorted_by_v.shape); sys.exit(0)
        symbList= ','.join(df_sorted_by_v.Symbol)
        return symbList
    pass


if __name__ == '__main__':
    logInit()
    s = TickerScreener()
    print(s.topNasdaq())
    sys.exit(0)
