#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *
import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime,timedelta,date
import matplotlib.pyplot as plt
import  datetime
import logging

from ibapi import wrapper,client, contract,scanner
import threading,queue
import socket

from pyhocon import ConfigFactory

import sys,time,inspect,os
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit
from gw.BaseGateway import BaseGateway
from gw.HistoricalDataLimitations import HistoricalDataLimitations





'''
    https://interactivebrokers.github.io/tws-api/client_wrapper.html#The


    Duration	        Allowed Bar Sizes
    60 S    	        1 sec - 1 mins
    120 S   	        1 sec - 2 mins
    1800 S (30 mins)	1 sec - 30 mins
    3600 S (1 hr)	    5 secs - 1 hr
    14400 S (4hr)	    10 secs - 3 hrs
    28800 S (8 hrs)	    30 secs - 8 hrs
    1 D	                1 min - 1 day
    2 D	                2 mins - 1 day
    1 W	                3 mins - 1 week
    1 M	                30 mins - 1 month
    1 Y	                1 day - 1 month




'''



class IBWrapper(wrapper.EWrapper):
    log = logging.getLogger("main.IBWrapper")
    def __init__(self):
        self.d_ = dict()
        super().__init__()
    def nextValidId(self,orderId):
        self.log.notice(f'IB connect 127.0.0.1: is established')
        pass

    def symbolSamples(self, reqId:int, contractDescriptions:'ListOfContractDescription'):
        super().symbolSamples(reqId,contractDescriptions)
        cnt = 0
        for c in contractDescriptions:
            s = c.contract.symbol
            print(f'{cnt}\t{s}')
            cnt += 1
        pass

    def scannerParameters(self, xml: str):
        super().scannerParameters(xml)
        open('log/scanner.xml', 'w').write(xml)
        print('scannerParameters done')


    def contractDetails(self, reqId:int, contractDetails:'ContractDetails'):
        msg = f' contractDetails( {reqId}:int, {contractDetails}:ContractDetails):'
        print(msg)
        self.d_['contract'] = contractDetails.contract
        pass
    def contractDetailsEnd(self, reqId:int):
        #msg = f'contractDetailsEnd(self, {reqId}:int)'
        #print(msg)
        pass

    def historicalNews(self, requestId:int, time:str, providerCode:str, articleId:str, headline:str):
        """returns historical news headlines"""
        print( f'{requestId}:int, {time}:str, {providerCode}:str, {articleId}:str, {headline}:str')

    def historicalNewsEnd(self, requestId:int, hasMore:bool):
        """signals end of historical news"""
        print( f'{requestId}:int, {hasMore}:bool')

    def newsProviders(self, newsProviders:'ListOfNewsProviders'):
        print('newsProviders :')
        for p in newsProviders:
            print(p)
        print('-'*10)


    def historicalData(self, reqId, bar):
        print(f'ReqId:{reqId} Time: {bar.date} Close: {bar.close}')

    def init_error(self):
        """ Place all of the error messages from IB into a Python queue, which can be accessed elsewhere.  """
        error_queue = queue.Queue()
        self.errors_ = error_queue
    def is_error(self):
        return not self.errors_.empty()
    def get_error(self,timeout=5):
        if not self.is_error():
            return None
        try:
            return self.errors_.get(timeout=timeout)
        except queue.Empty:
            return None


    def init_time(self):
        time_queue = queue.Queue()
        self.time_queue_ = time_queue
        return self.time_queue_
    def currentTime(self, server_time):
        self.time_queue_.put(server_time)
    pass

class IBClient(client.EClient):
    MAX_WAIT_TIME_SECS = 10
    def __init__(self, wrapper):
        super().__init__(wrapper)
    def obtain_server_time(self):
        #init the Q
        time_queue = self.wrapper.init_time()
        self.reqCurrentTime()
        try:
            server_time = time_queue.get( timeout=IBClient.MAX_WAIT_TIME_SECS)
        except queue.Empty:
            print(
                "Time queue was empty or exceeded maximum timeout of "
                "%d seconds" % IBAPIClient.MAX_WAIT_TIME_SECONDS
            )
            server_time = None
        while self.wrapper.is_error():
            print(self.get_error())
        return server_time






        pass
    pass

class GwIB(IBWrapper, IBClient, BaseGateway):
    log = logging.getLogger("main.GwIB")
    def __init__(self, config):
        '''
        >>> confPath = '../conf/v-trade.utest.conf'
        >>> c = ConfigFactory.parse_file(confPath)
        >>> #gw = GwIB(c)
        >>> #gw.disconnect()
        '''
        BaseGateway.__init__(self,config)
        self.port_ = self.c_.ib.port
        self.clientId_ = self.c_.ib.client_id
        IBWrapper.__init__(self)
        IBClient.__init__(self,wrapper=self)


        self.conditionVar_ =  threading.Condition()
        self.dataMsg_      = None

        # Listen for the IB responses
        self.init_error()
        self.connected_ = False
        self.log.debug(f'Make connect 127.0.0.1:{self.port_} clientId:{self.clientId_}')
        self.connect('127.0.0.1', self.port_, clientId=self.clientId_)
        self.connected_ = True

        thread = threading.Thread(target=self.run)
        thread.start()
        setattr(self, "_thread", thread)
        self.log.debug(f'New Thread {thread} with GwIB has been created ')
        self.histLimits_ = HistoricalDataLimitations(self.c_,source='ib')
        self.reqIdToSymbol_ = dict()
        self.initialize_signal_handlers()

        #time.sleep(2)
        pass

    def getHistoricalData(self,symbols, secType = 'STK',
        endDateTime='',
        durationString='3 M', barSizeSetting='5 mins',
        whatToShow = 'TRADES', useRTH=1,formatDate=1,
        timeout=36000
    ):
        '''
        https://interactivebrokers.github.io/tws-api/contract_details.html
        >>> confPath = '../conf/v-trade.utest.conf'
        >>> c = ConfigFactory.parse_file(confPath)
        >>> gw = GwIB(c)
        >>> symbols = c.ticker.stock.us.cn
        >>> symbols = ','.join(symbols)
        >>> symbols = 'WB,NIO'
        >>> ret = gw.getHistoricalData(symbols)
        >>> gw.disconnect()
        >>> ret
        123
        '''
        #reqHistoricalData(12, c, '', '2 D', '1 hour', 'TRADES',useRTH=0,formatDate=1,keepUpToDate=False, chartOptions=[])
        contractDict = self.batchReqContractDetails(symbols, secType)
        assert contractDict is not None
        reqId = 100
        self.dataMsg_ = dict()
        for s,c in contractDict.items():
            self.histLimits_ .wait('reqHistoricalData', s)

            self.log.debug(f'self.reqHistoricalData({reqId}, s, {endDateTime}, {durationString}, {barSizeSetting} ,whatToShow={whatToShow},...')
            self.reqHistoricalData(reqId, c, endDateTime, durationString, barSizeSetting ,whatToShow=whatToShow,
                useRTH=useRTH,formatDate=formatDate,keepUpToDate=False, chartOptions=[])
            self.histLimits_ .logCall('reqHistoricalData', s)
            self.reqIdToSymbol_[reqId] =s
            reqId += 1
            pass
        ret = self.waitAllReqDoneOrTimeout(contractDict.keys(), timeout=timeout)
        if ret is None:
            return ret
        self.log.debug(f'Finish All')
        for r,s in self.reqIdToSymbol_.items():
            df = self.dataMsg_[r]
            print(s)
            display(df)

        ret = self.dataMsg_
        self.dataMsg_ = None
        return ret

    def historicalData(self, reqId, bar):
        o = {'date':bar.date, 'open': bar.open, 'high':bar.high, 'low': bar.low, 'close':bar.close, 'volume':bar.volume, 'wap':bar.average}
        if reqId not in self.dataMsg_:
            self.dataMsg_[reqId] = []
        self.dataMsg_[reqId].append(o)
        pass

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        symbol = self.reqIdToSymbol_[reqId]
        s = start.split()[0]
        e = end.split()[0]
        filePath = f'../data/{symbol}-{s}-{e}.csv'
        df = pd.DataFrame( self.dataMsg_[reqId] ).sort_values(by='date')
        df.to_csv(filePath, index=False)
        self.dataMsg_[reqId] = df
        self.log.warning(f'Write file {filePath}')
        with self.conditionVar_:
            self.conditionVar_.notify()
        pass



    def batchReqContractDetails(self,symbols, secType = 'STK'):
        '''
        https://interactivebrokers.github.io/tws-api/contract_details.html
        >>> confPath = '../conf/v-trade.utest.conf'
        >>> c = ConfigFactory.parse_file(confPath)
        >>> gw = GwIB(c)
        >>> symbols = c.ticker.stock.us.cn
        >>> symbols = ','.join(symbols)
        >>> gw.batchReqContractDetails(symbols)
        >>> gw.disconnect()
        '''
        symList = symbols.replace(',',' ').split()
        cList   = []
        reqId = 100
        self.dataMsg_     = dict()
        self.reqIdToSymbol_ = dict()
        for sym in symList:
            c  = contract.Contract()
            c.symbol = sym
            c.secType = secType
            c.exchange ='SMART'
            c.currency ='USD'
            cList.append(c)
            self.log.debug(f'Call reqContractDetails({reqId}, {c.symbol}, {c.exchange},{c.currency}, )')
            self.reqContractDetails(reqId, c)
            self.reqIdToSymbol_[reqId] = sym
            reqId += 1
        ret = self.waitAllReqDoneOrTimeout(symList, timeout=120)
        if ret is None:
            return ret

        self.log.debug(f'Finish All')
        ret = self.dataMsg_
        self.dataMsg_ = None
        return ret

    def contractDetails(self, reqId:int, contractDetails:'ContractDetails'):
        with self.conditionVar_:
            c  = contractDetails.contract
            self.dataMsg_ [c.symbol] =c
            self.conditionVar_.notify()
            self.log.debug(f'Received contract({reqId}, {c.symbol})')
        pass
    def waitAllReqDoneOrTimeout(self, originalSet, timeout=300):
        start = time.time()
        cnt = 0
        totalNum = len(originalSet)

        def getRemainSet():
            setTotal = set(originalSet)
            setDone  = set(self.dataMsg_.keys())
            setRemain = ','.join( setTotal - setDone)
            return setRemain

        while time.time() - start < timeout and cnt < totalNum:
            with self.conditionVar_:
                self.log.debug('wait a condition')
                self.conditionVar_.wait(timeout=timeout)
                cnt = len(self.dataMsg_.keys())
                self.log.debug('After wait the condition')
                if  (totalNum - cnt) < 5:
                    setRemain = getRemainSet()
                    self.log.debug(f'Remained symbols or reqIds {setRemain}')
            self.log.debug(f'Finish {cnt}/{totalNum}')
        if cnt != totalNum:
            setTotal = set(originalSet)
            setRemain = getRemainSet()
            msg = f'Some contract details got failed {setRemain}'
            self.log.critical(msg)
            return None
        return cnt


    def symbolSamples(self, reqId:int, contractDescriptions:'ListOfContractDescription'):
        super().symbolSamples(reqId,contractDescriptions)
        cnt = 0
        for c in contractDescriptions:
            s = c.contract.symbol
            print(f'{cnt}\t{s}')
            cnt += 1
        pass


    def nextValidId(self,orderId):
        if not self.connected_ :
            self.connected_ = True
            self.log.notice(f'IB connect 127.0.0.1:{self.port_} clientId:{self.clientId_} is established')
        pass
    def reconnect(self):
        if not self.c_.ib.auto_connect:
            return
        self.log.debug(f'reconnect the ib gw after {self.c_.ib.auto_connect_timer} seconds')
        time.sleep(self.c_.ib.auto_connect_timer)
        self.log.debug(f'Make connect 127.0.0.1:{self.port_} clientId:{self.clientId_}')
        self.connect('127.0.0.1', self.port_, clientId=self.clientId_)
        self.connected_ = True
        pass
    def error(self, reqId:'TickerId', errorCode:int, errorString:str):
        """This event is called when there is an error with the communication or when TWS wants to send a message to the client."""
        errMsg = f'IB ERR (id:{reqId}, code:{errorCode},str:{errorString})'
        self.errors_.put(errMsg)
        self.log.error(errMsg)
        if errorCode == 502:
            self.connected_ = False
            self.reconnect()


    def initialize_signal_handlers(self):
        import signal
        def handle_sighup(signum, frame):
            self.log.info("received SIGHUP")
            self.sighup_received = True

        def handle_sigterm(signal, frame):
            self.log.info("received SIGTERM")
            self.sigterm_received = True

        def handle_sigint(signal, frame):
            self.log.info("received SIGINT")
            self.sigint_received = True

        #signal.signal(signal.SIGTERM, handle_sigterm)
        signal.signal(signal.SIGHUP, handle_sighup)
        signal.signal(signal.SIGINT, handle_sigint)


    pass


if __name__ == '__main__':
    logInit()
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        import doctest; doctest.testmod(); sys.exit(0)

    confPath = '../conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)
    gw = GwIB(c)
    symbols = c.ticker.stock.us.top_150V
    symbols = c.ticker.stock.us.cn
    symbols = ','.join(symbols)
    symbols = 'WB,NIO'
    #ret = gw.getHistoricalData(symbols, endDateTime='20210924  09:30:00')
    ret = gw.getHistoricalData(symbols,durationString='5 D',barSizeSetting='1 min', endDateTime='')
    #ret = gw.getHistoricalData(symbols,durationString='3 D', endDateTime='')
    gw.disconnect()

    sys.exit(0)
