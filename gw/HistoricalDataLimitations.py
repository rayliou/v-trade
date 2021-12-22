#!/usr/bin/env python3
# coding=utf-8
#from futu import *
from IPython.display import display, HTML
#import talib
from pyhocon import ConfigFactory
import sys,time,inspect,os,os.path
import glob,re
import hashlib
import logging,json
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit



class HistoricalDataLimitations:
    log = logging.getLogger("main.HistoricalDataLimitations")
    '''
    https://interactivebrokers.github.io/tws-api/historical_limitations.html

    '''
    def __init__(self, conf, source='ib'):
        self.c_ = conf
        self.limit_ = self.c_[source].hist_data.limit
        self.msgCalled_ = []

    def wait(self, callName, symbol):
        allow  = self.allow(callName, symbol)
        while not allow:
            time.sleep(1)
            allow  = self.allow(callName, symbol)
        pass

    def allow(self, callName, symbol):
        '''
        >>> confPath = '../conf/v-trade.utest.conf'
        >>> c = ConfigFactory.parse_file(confPath)
        >>> l = HistoricalDataLimitations(c)
        >>> l.logCall('c1', 's1')
        >>> l.logCall('c3', 's2')
        >>> time.sleep(1)
        >>> l.allow('c1', 's1')
        False
        >>> l.allow('c1', 's2')
        True
        >>> l.allow('c3', 's2')
        False
        >>> l.allow('c4', 's2')
        True
        >>> time.sleep(1.1)
        >>> l.allow('c1', 's2')
        True
        >>> time.sleep(2)
        >>> l.allow('c1', 's1')
        True
        >>> l.logCall('c1', 's2')
        >>> time.sleep(6)
        >>> l.logCall('c2', 's2')
        >>> l.logCall('c3', 's2')
        >>> l.logCall('c4', 's2')
        >>> l.allow('c1', 's1')
        True
        '''
        tm = time.time()
        i  = 0
        removedIndex = set()
        cntTotal              = 0
        cntSameCall       = 0
        cntSameCallAndSymbol  = 0
        for c in  self.msgCalled_:
            tmDiff  =  tm - c[2]
            self.log.debug(f'Time diff:{tmDiff}')
            if tmDiff > self.limit_.global_call.time_span:
                removedIndex.add(i)
            else:
                cntTotal += 1
                if c[0] == callName:
                    if tmDiff <= self.limit_.same_call.time_span:
                        cntSameCall     +=1
                    if c[1] == symbol:
                        if tmDiff <= self.limit_.same_call_and_sym.time_span:
                            cntSameCallAndSymbol  += 1
            i += 1
            pass
        for i in removedIndex:
            del self.msgCalled_[i]
        b1 = cntTotal < self.limit_.global_call.max_call
        b2 = cntSameCall < self.limit_.same_call.max_call
        b3 = cntSameCallAndSymbol < self.limit_.same_call_and_sym.max_call
        msg = f'{callName} {symbol}: cntTotal {cntTotal} {b1}  , cntSameCall {cntSameCall} {b2}, cntSameCallAndSymbol {cntSameCallAndSymbol} {b3}'
        self.log.debug(msg)
        return b1 and b2 and b3



    def logCall(self, callName, symbol):
        tm = time.time()
        self.msgCalled_.append((callName, symbol,tm))
        pass
    pass

if __name__ == '__main__':
    logInit()
    import doctest; doctest.testmod(); sys.exit(0)
    sys.exit(0)
