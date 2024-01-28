#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *
import sys,time

import yfinance as yf
import numpy as np
import pandas as pd
from pyhocon import ConfigFactory
from  BaseGateway import BaseGateway

import sys,time,inspect,os
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit
import finnhub


'''
https://finnhub.io/docs/api
https://finnhub.io/docs/api/stock-splits
'''

class GwFinnhub(BaseGateway):
    def __init__(self, config):
        '''
        >>> confPath = '../conf/v-trade.utest.conf'
        >>> c = ConfigFactory.parse_file(confPath)
        >>> gw = GwFinnhub(c)
        >>> r  = gw.getHistoricalData('NIO')
        >>> r
        '''
        BaseGateway.__init__(self,config)
        #print( self.c_.finnhub.api_key)
        self.fClient_ = finnhub.Client(api_key=self.c_.finnhub.api_key)

        pass
    def getHistoricalData(self, symbol):
        resolution  = 5 #1, 5, 15, 30, 60, D, W, M
        t    = int(time.time())
        f  = t - 1 * 24 *3600
        ret  = self.fClient_ .stock_candles(symbol, resolution ,f,t)
        return ret

    pass


if __name__ == '__main__':
    logInit()
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        import doctest; doctest.testmod(); sys.exit(0)

    sys.exit(0)
