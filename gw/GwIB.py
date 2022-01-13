#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *
import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime,timedelta,date
import matplotlib.pyplot as plt
import logging

from ibapi import wrapper,client, contract,scanner
from ibapi.ticktype import TickTypeEnum,TickType

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

import click,glob

from functools import wraps



HistoricalDataLimitations = '''
    https://interactivebrokers.github.io/tws-api/client_wrapper.html#The
    https://interactivebrokers.github.io/tws-api/historical_limitations.html#non-available_hd


    Duration	        Allowed Bar Sizes
    \b 60 S    	        1 sec - 1 mins
    \b 120 S   	        1 sec - 2 mins
    \b 1800 S (30 mins)	1 sec - 30 mins
    \b 3600 S (1 hr)	    5 secs - 1 hr
    \b 14400 S (4hr)	    10 secs - 3 hrs
    \b 28800 S (8 hrs)	    30 secs - 8 hrs
    \b 1 D	                1 min - 1 day
    \b 2 D	                2 mins - 1 day
    \b 1 W	                3 mins - 1 week
    \b 1 M	                30 mins - 1 month
    \b 1 Y	                1 day - 1 month




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
    callsCurSec = []
    @classmethod
    def speedControl(cls, function, callsList, maxCalls =3, seconds=1):
        def refreshAndWait():
            total = len(callsList)
            while total >= maxCalls:
                tm = time.time()
                while total > 0 and  (tm - callsList[0]) >= seconds:
                    del callsList[0]
                    total = len(callsList)
                time.sleep(0.1)
            return total
        @wraps(function)
        def wrapper(*args, **kwargs):
            cls.log.debug(f'before call {function.__name__}, totalSecondCalls= {len(callsList)}')
            refreshAndWait()
            tm = time.time()
            ret =  function(*args, **kwargs)
            callsList.append(tm)
            cls.log.debug(f'After call {function.__name__}, totalSecondCalls= {len(callsList)}')
            return ret

        return wrapper
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
        self.source_ = 'ib'
        IBWrapper.__init__(self)
        IBClient.__init__(self,wrapper=self)


        self.conditionVar_ =  threading.Condition()
        self.rcvDatabyreqIds_      = None

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
        #self.histLimits_ = HistoricalDataLimitations(self.c_,source='ib')

        self.semHistCall_ = threading.Semaphore(50)
        self.semMktDataCall_ = threading.Semaphore(80)
        self.reqIdToSymbol_ = dict()
        self.initialize_signal_handlers()
        self.cntCallHistoricalData_ = 0

        self.reqContractDetails = GwIB.speedControl(self.reqContractDetails,GwIB.callsCurSec, 49,1)
        self.reqHistoricalData = GwIB.speedControl(self.reqHistoricalData,GwIB.callsCurSec, 49,1)
        self.liveHookFunc_ = None

        #time.sleep(2)
        pass

    def getHistoricalData(self,symbols, secType = 'STK',
        endDateTime='',
        durationString='3 M', barSizeSetting='5 mins',
        whatToShow = 'TRADES', useRTH=1,formatDate=1,
        timeout=60,keepUpToDate=False
    ):
        '''
        https://interactivebrokers.github.io/tws-api/historical_limitations.html#hd_step_sizes
        '''
        #reqHistoricalData(12, c, '', '2 D', '1 hour', 'TRADES',useRTH=0,formatDate=1,keepUpToDate=False, chartOptions=[])
        cdsList = self.getContractDetails(symbols, secType)
        assert cdsList is not None
        reqId = 100
        self.rcvDatabyreqIds_ = dict(); reqId = 100
        self.reqIdToSymbol_ = dict()
        self.rcvDfBigTableHist_ = None
        self.keepUpToDate_ = keepUpToDate
        cnt  = 1
        for cds in cdsList:
            #self.histLimits_ .wait('reqHistoricalData', s)
            c = cds.contract
            s = c.symbol
            self.log.debug('semHistCall_ .acquire()')
            self.semHistCall_ .acquire()
            self.log.debug(f'self.reqHistoricalData({reqId}, s, {endDateTime}, {durationString}, {barSizeSetting} ,whatToShow={whatToShow}, keepUpToDate={keepUpToDate}...')
            self.reqHistoricalData(reqId, c, endDateTime, durationString, barSizeSetting ,whatToShow=whatToShow,
                useRTH=useRTH,formatDate=formatDate,keepUpToDate=keepUpToDate, chartOptions=[])
            #self.histLimits_ .logCall('reqHistoricalData', s)
            self.reqIdToSymbol_[reqId] =s
            reqId += 1
            pass
        start = time.time()
        total = len(self.reqIdToSymbol_)
        numDone = 0 if self.rcvDfBigTableHist_  is None else len(set(self.rcvDfBigTableHist_.columns.get_level_values(0)))
        while (time.time() - start < timeout) and numDone < total:
            time.sleep(1)
            with self.conditionVar_:
                numDone = 0 if self.rcvDfBigTableHist_  is None else len(set(self.rcvDfBigTableHist_.columns.get_level_values(0)))

        df =  self.rcvDfBigTableHist_
        self.rcvDfBigTableHist_ = None
        return df

    def setLiveHookFunc(self, func, *lArgs, **dArgs):
        self.liveHookFunc_ = func
        self.liveHookFuncArgs_ = (lArgs, dArgs)
        self.log.debug(f'setLiveHookFunc:{self.liveHookFunc_} {self.liveHookFuncArgs_}')
        pass
    def historicalDataUpdate(self, reqId, bar):
        o = {'date':bar.date, 'open': bar.open, 'high':bar.high, 'low': bar.low, 'close':bar.close, 'volume':bar.volume, 'wap':bar.average}
        if self.liveHookFunc_ is not None:
            symbol = self.reqIdToSymbol_[reqId]
            self.log.debug( f'reqId:{reqId}; symbol:{symbol} date:{bar.date}' )
            self.liveHookFunc_(symbol,bar,self.liveHookFuncArgs_[0],self.liveHookFuncArgs_[1])
        pass

    def historicalData(self, reqId, bar):
        o = {'date':bar.date, 'open': bar.open, 'high':bar.high, 'low': bar.low, 'close':bar.close, 'volume':bar.volume, 'wap':bar.average}
        if self.liveHookFunc_ is not None:
            symbol = self.reqIdToSymbol_[reqId]
            self.log.debug( f'reqId:{reqId}; symbol:{symbol} date:{bar.date}' )
            self.liveHookFunc_(symbol,bar,self.liveHookFuncArgs_[0],self.liveHookFuncArgs_[1])
        if reqId not in self.rcvDatabyreqIds_:
            self.rcvDatabyreqIds_[reqId] = []
        self.rcvDatabyreqIds_[reqId].append(o)
        self.cntCallHistoricalData_  += 1
        if self.cntCallHistoricalData_ % 100 == 0:
            self.log.debug( f'reqId:{reqId}; date:{bar.date}' )
        pass

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        if self.liveHookFunc_ is not None:
            return

        thread = threading.Thread(target=self.threadHistoricalDataEnd, args=(reqId, start, end),daemon=True)
        thread.start()
        self.semHistCall_ .release()
        self.log.debug('semHistCall_ .release()')
        pass

    def threadHistoricalDataEnd(self, reqId:int, start:str, end:str):
        symbol = self.reqIdToSymbol_[reqId]
        s = start.split()[0]
        e = end.split()[0]
        df = pd.DataFrame( self.rcvDatabyreqIds_[reqId] ).sort_values(by='date')
        df.date = pd.to_datetime(df.date)
        df.set_index('date', drop=True, inplace=True)
        self.rcvDatabyreqIds_[reqId] = df
        df.columns = pd.MultiIndex.from_product([[symbol],df.columns, ])
        with self.conditionVar_:
            if self.rcvDfBigTableHist_ is None:
                self.rcvDfBigTableHist_  = df
            else: #merge
                assert symbol not in self.rcvDfBigTableHist_.columns
                self.rcvDfBigTableHist_  =  pd.merge_asof(self.rcvDfBigTableHist_ , df, right_index=True, left_index=True, suffixes=('',''))
            self.conditionVar_.notify()

        setDone = set(self.rcvDfBigTableHist_.columns.get_level_values(0))
        setAll = set(self.reqIdToSymbol_.values())
        #msg = f'[{len(setAll)-len(setDone)}/{len(setAll)}]:\t Waiting:[{",".join(setAll -setDone)} ], 1st line[{self.dfBigTableHist_.iloc[0]}]'
        msg = f'[{len(setAll)-len(setDone)}/{len(setAll)}]:\t Waiting:[{",".join(setAll -setDone)} ]'
        self.log.warning(msg)
        self.log.warning(f'Merged:{symbol}-{start}-{end}[{df.index[0]}:{df.index[-1]}], reqId:{reqId}')
        del self.rcvDatabyreqIds_[reqId]
        df = None
        pass

    def watchPosition(self,dfPairs):
        thread = threading.Thread(target=self.trdWatchPosition, args=(dfPairs,))
        thread.start()
        self.log.debug('Create thread trdWatchPosition and wait')
        thread.join()
        pass
    def trdWatchPosition(self,dfPairs):
        while True:
            time.sleep(2)
            self.dataPosition_ = None
            maxTimeout = 60
            start  = time.time()
            symbToreqIds = dict()
            with self.conditionVar_:
                self.reqPositions()
                self.log.debug('wait a condition for reqPositions')
                self.conditionVar_.wait(timeout=60)
                if self.dataPosition_ is None:
                    continue
                del self.dataPosition_['700']
                self.rcvDatabyreqIds_ = dict(); reqId = 100
                for s,v in self.dataPosition_.items():
                    v['c'].exchange ='SMART'
                    #self.reqMktData(reqId,v['c'], '221', snapshot=True,regulatorySnapshot=False,mktDataOptions=[])
                    self.log.debug('semMktDataCall_ .acquire()')
                    self.semMktDataCall_ .acquire()
                    self.log.debug(f'Call self.reqMktData({reqId},{v["c"].symbol}, "", True, False, [])')
                    self.reqMktData(reqId,v['c'], "", True, True, [])
                    symbToreqIds[s] = reqId
                    reqId += 1
                while maxTimeout > (time.time() -start) and len(self.rcvDatabyreqIds_) < len(self.dataPosition_):
                    self.log.debug('wait a condition for reqMktData')
                    self.conditionVar_.wait(timeout=60)
            for k,v in self.dataPosition_.items():
                reqId = symbToreqIds[k]
                v['price'] = self.rcvDatabyreqIds_[reqId]['price']
            dfPosition = pd.DataFrame(self.dataPosition_).T
            dfPosition.drop(['c'], axis=1,inplace=True)
            oList  = []
            for index, row in dfPairs.iterrows():
                n1 = row['n1']
                n2 = row['n2']
                if n1 not in symbToreqIds or n2 not in symbToreqIds:
                    continue
                s = row['slope']
                m = row['m']
                std = row['std']
                i = row['i']
                o = {
                        'n1':  n1,
                        'n2':  n2,
                        'st':  std,
                        'x_price':  self.dataPosition_[n1]['price'],
                        'x_price':  self.dataPosition_[n1]['price'],
                        'x_pos':  self.dataPosition_[n1]['position'],
                        'y_price':  self.dataPosition_[n2]['price'],
                        'y_pos':  self.dataPosition_[n2]['position'],
                        }
                o['z_diff'] = (o['x_price'] * s +i - o['y_price'] -m)/std
                if abs(o['x_pos']) <1 or abs(o['y_pos']) < 1:
                    continue
                oList.append(o)
            dfO = pd.DataFrame(oList)
            display(dfO)
        pass

    def position(self, account:str, contract:'Contract', position:float, avgCost:float):
        """This event returns real-time positions for all accounts in
        response to the reqPositions() method."""
        if self.dataPosition_ is None:
            self.dataPosition_ = dict()
        self.dataPosition_ [contract.symbol] = {'c': contract, 'position': position, 'avgCost': avgCost, 'account': account }
        pass

    def positionEnd(self):
        """This is called once all position data for a given request are
        received and functions as an end marker for the position() data. """
        with self.conditionVar_:
            self.conditionVar_.notify()
        pass

    def getSnapshot(self, symbolsList,cdsList=None ):
        symbols = symbolsList
        if cdsList is None:
            cdsList = self. getContractDetails(symbols, secType='STK')
        assert cdsList is not None
        self.rcvDatabyreqIds_ = dict()
        reqIdToSymbols = dict(); self.rcvDatabyreqIds_ = dict(); reqId = 100
        cnt  = 1
        for cds in cdsList:
            c = cds.contract
            s = c.symbol
            c.exchange ='SMART'
            self.log.debug('semMktDataCall_ .acquire()')
            self.semMktDataCall_ .acquire()
            self.log.debug(f'Call self.reqMktData({reqId},{c.symbol}, "", True, False, [])')
            self.reqMktData(reqId,c, "", True, True, [])
            reqIdToSymbols[reqId] = s
            if cnt % 90 == 0:
                time.sleep(1)
            cnt += 1; reqId += 1

        maxTimeout = 10
        start  = time.time()
        while maxTimeout > (time.time() -start) and len(self.rcvDatabyreqIds_) < len(cdsList):
            self.log.debug('wait a condition for reqMktData')
            with self.conditionVar_:
                self.conditionVar_.wait(timeout=maxTimeout)
        oList  = []
        snapDict  = dict()
        #for s in contractDict.keys():
        for reqId in self.rcvDatabyreqIds_.keys():
            s = reqIdToSymbols[reqId]
            #v['price'] = self.rcvDatabyreqIds_[reqId]['price']
            snapDict[s] =  self.rcvDatabyreqIds_[reqId]
        df  = pd.DataFrame(snapDict).T[['BID','ASK','LAST','CLOSE']]
        df = df[(df.BID >3 )& (df.ASK >3) & (df.LAST>3)]
        return df, cdsList

    def tickPrice(self, reqId:'TickerId' , tickType:TickType, price:float, attrib:'TickAttrib'):
        """Market data tick price callback. Handles all price related ticks."""
        if reqId not in self.rcvDatabyreqIds_ :
            self.rcvDatabyreqIds_[reqId] = dict()
        tickType = TickTypeEnum.to_str(tickType)
        self.rcvDatabyreqIds_[reqId][tickType] = price
        #self.rcvDatabyreqIds_[reqId]['tickType'] = tickType
        #self.rcvDatabyreqIds_[reqId]['price'] = price
        #self.rcvDatabyreqIds_[reqId]['attrib'] = attrib
        pass


    def tickSize(self, reqId:'TickerId', tickType:'TickType', size:int):
        """Market data tick size callback. Handles all size-related ticks."""
        if reqId not in self.rcvDatabyreqIds_ :
            self.rcvDatabyreqIds_[reqId] = dict()
        #self.rcvDatabyreqIds_[reqId]['tickType'] = tickType
        #self.rcvDatabyreqIds_[reqId]['size'] = size
        pass

    def tickSnapshotEnd(self, reqId:int):
        """When requesting market data snapshots, this market will indicate the
        snapshot reception is finished. """
        self.semMktDataCall_ .release()
        with self.conditionVar_:
            self.conditionVar_.notify()
        self.log.debug(f'tickSnapshotEnd({reqId})')
        pass

    def writeHistoricalBigTableToFile(self):
        BaseGateway.writeHistoricalBigTableToFile(self,self.conditionVar_)
        pass


    def getContractDetails(self,symbols, secType = 'STK', timeout=20) -> list:
        #symList = symbols.replace(',',' ').split()
        symList = symbols
        cList   = []
        self.rcvDatabyreqIds_     = dict()
        reqIdToSymbols = dict(); self.rcvDatabyreqIds_ = dict(); reqId = 100
        cnt  = 1
        for sym in symList:
            c  = contract.Contract()
            c.symbol = sym
            c.secType = secType
            c.exchange ='SMART'
            c.currency ='USD'
            cList.append(c)
            self.log.debug(f'Call reqContractDetails({reqId}, {c.symbol}, {c.exchange},{c.currency}, )')
            self.reqContractDetails(reqId, c)
            reqIdToSymbols[reqId] = sym
            reqId += 1
        start = time.time()
        total = len(reqIdToSymbols)
        while (time.time() - start < timeout) and len(self.rcvDatabyreqIds_) < total:
            time.sleep(0.1)
        return [cds for cds in self.rcvDatabyreqIds_.values()]

    def contractDetails(self, reqId:int, contractDetails:'ContractDetails'):
        c  = contractDetails.contract
        if reqId not in self.rcvDatabyreqIds_ :
            self.rcvDatabyreqIds_[reqId] = dict()
        self.rcvDatabyreqIds_[reqId] = contractDetails
        self.log.debug(f'Received contract({reqId}, {c.symbol})')

        pass
    # def waitAllReqDoneOrTimeout(self, originalSet, timeout=300):
    #     start = time.time()
    #     cnt = 0
    #     totalNum = len(originalSet)

    #     def getRemainSet():
    #         setTotal = set(originalSet)
    #         setDone  = set(self.dataMsg_.keys())
    #         setRemain = ','.join( setTotal - setDone)
    #         return setRemain

    #     while time.time() - start < timeout and cnt < totalNum:
    #         with self.conditionVar_:
    #             self.log.debug('wait a condition')
    #             self.conditionVar_.wait(timeout=timeout)
    #             cnt = len(self.dataMsg_.keys())
    #             self.log.debug('After wait the condition')
    #             if  (totalNum - cnt) < 5:
    #                 setRemain = getRemainSet()
    #                 self.log.debug(f'Remained symbols or reqIds {setRemain}')
    #         self.log.debug(f'Finish {cnt}/{totalNum}')
    #     if cnt != totalNum:
    #         setTotal = set(originalSet)
    #         setRemain = getRemainSet()
    #         msg = f'Some contract details got failed {setRemain}'
    #         self.log.critical(msg)
    #         return None
    #     return cnt


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
            self.writeHistoricalBigTableToFile()

        def handle_sigterm(signal, frame):
            self.log.info("received SIGTERM")
            self.sigterm_received = True

        def handle_sigint(signal, frame):
            self.log.info("received SIGINT")
            self.sigint_received = True

        #signal.signal(signal.SIGTERM, handle_sigterm)
        signal.signal(signal.SIGHUP, handle_sighup)
        #signal.signal(signal.SIGINT, handle_sigint)


    pass

@click.command()
#@click.option('--src',  help='src')
#@click.option('--dst',  help='dst')
def watchPosition():
    confPath = '../conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)
    gw = GwIB(c)
    # def fillMktPrice(df, symCols:list):
    #     slist = pd.concat([df[s] for s in symCols ])
    #     symList = ' '.join(set(slist))
    #     ibkr = IBKR()
    #     dfR  = ibkr.reqMktData(symList)[['markPrice','close']]
    #     for s in symCols:
    #         df  = df.join(dfR, on=s)
    #         df['x_'+s] = df.markPrice
    #         df.drop(['markPrice', 'close'], axis=1,inplace=True)
    #     d = df.x_n1 * df.slope + df.i - df.x_n2 - df.m
    #     df['d'] = d
    #     df['z']    = d/df['std']
    #     df = df[df.slope > 0]
    #     df = df[(df.z > 1.9) | (df.z <-1.9)].sort_values(by='z')
    #     return df
    #     pass

    files = glob.glob('../202*/lineregress*.csv')
    dfs = [ pd.read_csv(f) for f in files]
    df  = pd.concat(dfs)
    #df = fillMktPrice(df,['n1', 'n2'])

    display(df)
    gw.watchPosition(df)
    pass

@click.command()
#@click.option('--src',  help='src')
#@click.option('--dst',  help='dst')
def getContractDetails():
    confPath = '../conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)
    symbols = c.ticker.stock.us.topV5000
    symbols = [s.replace('/',' ') for s in symbols]
    symbols = symbols[0:300]
    gw = GwIB(c)
    cdsList = gw.getContractDetails(symbols, 'STK')
    print(cdsList)

    gw.disconnect()
    #display(df)
    pass

@click.command()
@click.argument('group')
@click.argument('dst')
@click.option('--duration',  help=HistoricalDataLimitations, default='3 D')
@click.option('--interval',  help='5 mins|1 min etc...', default='5 mins')
@click.option('--timeout',  help='default:60 by seconds', default=60)
def downloadHistory(group, dst, duration, interval, timeout):
    confPath = '../conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)
    symbols = c.ticker.stock.us[group]
    symbols = [s.replace('/',' ') for s in symbols]
    gw = GwIB(c)
    df = gw.getHistoricalData(symbols, 'STK', durationString=duration, barSizeSetting=interval, timeout=timeout)
    df.to_csv(dst)
    display(df.head(1))
    display(df.tail(1))
    gw.disconnect()
    #display(df)
    pass

@click.command()
@click.argument('src', nargs=-1)
@click.argument('dst')
def merge_df(src, dst):
    v  = [ pd.read_csv(f,index_col=0, header=[0,1], parse_dates=True).dropna() for f in src]
    df = pd.concat(v).sort_values(by='date')
    df[~df.index.duplicated(keep='first')].dropna(1, 'any')
    df.to_csv(dst)


@click.command()
@click.argument('x')
@click.argument('y')
@click.option('-s','--slope',  help='', type=float)
@click.option('-i','--intercept',  help='', type=float)
@click.option('-m','--mean',  help='', default=0, type=float)
@click.option('--std',  help='', default=0, type=float)
def plotLivePair(x,y,slope,intercept,mean,std):
    logInit(logging.ERROR)
    confPath = '../conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)
    gw = GwIB(c)
    fig = plt.figure(figsize = (12,8))
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    ax = fig.add_subplot(111)
    #diff.plot(ax=ax)
    symbols = [x,y]
    MAX_NUM = 720
    timeS = {x:[], y:[]}

    def updatePairs():
        if len(timeS[x]) == 0 or len(timeS[y]) == 0:
            return
        for xVal in reversed(timeS[x]):
            for yVal in reversed(timeS[y]):
                if xVal.date == yVal.date:
                    d = slope * xVal.close + intercept - yVal.close
                    z = (d - mean)/std
                    print(z)
                    return z
        return None



    def reDraw(symbol,bar, *arg,**kwargs ):
        bars = timeS[symbol]
        bars.append(bar)
        if len(bars) > MAX_NUM:
            del bars[0]
        # print(timeS[symbol][-1])
        updatePairs()
        pass

        #print(symbol)
        #print(f'symbol:{symbol}, data:{data}, ax:{ax}')
        #return None
        # ax.axhline(mean+std*2, color='g', linestyle='--', label= f'Sell {x}/Buy {y}')
        #ax.axhline(mean-std*2, color='r', linestyle='--', label= f'Buy {x}/Sell {y}')
        #ax.axhline(mean-std, color='y', linestyle='--')
        #ax.axhline(mean+std, color='y', linestyle='--')
        #ax.axhline(mean,  linestyle='--')
        #ax.set_title(f'+:{n1} short {n1}+ long {n2};-:short {n2}+ long {n1};')
        # plt.legend()
        # plt.pause(0.05)
        # plt.show()
        pass

    gw.setLiveHookFunc(reDraw,ax=ax)
    gw.getHistoricalData(symbols, 'STK', durationString='3600 S', barSizeSetting='5 secs',useRTH=0, keepUpToDate=True)
    pass


@click.command()
def web():
    from flask import Flask, render_template
    from flask_socketio import SocketIO
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)
    @app.route('/')
    def hello():
        return '<H1>Hello World </H1>'
    socketio.run(app)
    pass



@click.group()
def cli():
    pass


if __name__ == '__main__':
    logInit()
    cli.add_command(getContractDetails)
    cli.add_command(watchPosition)
    cli.add_command(downloadHistory)
    cli.add_command(merge_df)
    cli.add_command(plotLivePair)
    cli.add_command(web)

    cli(); sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        import doctest; doctest.testmod(); sys.exit(0)
