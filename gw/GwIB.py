#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *
import sys,time,inspect,os
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
import BaseGateway

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit





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

def getOpenedPort():
    from contextlib import closing
    def check_socket(host, port):
        ret = False
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            ret = sock.connect_ex((host, port)) == 0
        return ret

    # TWS  7496     7497
    # GW   4001     4002
    for p in [7497,4002,4001,7496]:
        isOpen = check_socket('127.0.0.1',p)
        print(f'Port: {p} => {isOpen}')
        if not isOpen:
            continue
        return p
    return -1



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

class GwIB(IBWrapper, IBClient, BaseGateway.BaseGateway):
    log = logging.getLogger("main.GwIB")
    def __init__(self, config):
        '''
        >>> confPath = '../conf/v-trade.utest.conf'
        >>> c = ConfigFactory.parse_file(confPath)
        >>> gw = GwIB(c)
        >>> gw.disconnect()
        >>> time.sleep(8)
        >>> gw
        '''
        BaseGateway.BaseGateway.__init__(self,config)
        self.port_ = self.c_.ib.port
        self.clientId_ = self.c_.ib.client_id
        IBWrapper.__init__(self)
        IBClient.__init__(self,wrapper=self)

        thread = threading.Thread(target=self.run)
        thread.start()
        setattr(self, "_thread", thread)
        self.log.debug(f'New Thread {thread} with GwIB has been created ')
        # Listen for the IB responses
        self.init_error()
        self.connected_ = False
        self.log.debug(f'Make connect 127.0.0.1:{self.port_} clientId:{self.clientId_}')
        self.connect('127.0.0.1', self.port_, clientId=self.clientId_)
        self.connected_ = True
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


    pass


if __name__ == '__main__':
    logInit()
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        import doctest; doctest.testmod(); sys.exit(0)

    sys.exit(0)
    # ports
    #      Live     Demo
    # TWS  7496     7497
    # GW   4001     4002
    #port = 7497
    port = 7496
    #port = getOpenedPort()
    ibApp = GwIB(port=port)
    print("Successfully launched IB API application...")
    ibApp.reqMatchingSymbols(1,'*');
    time.sleep(100); ibApp.disconnect(); sys.exit(0)

    def genContractsFromSymsList(self, symList):
        symList = symList.replace(',',' ').split()
        cList   = []
        for sym in symList:
            c  = contract.Contract()
            c.symbol = sym
            c.sectype ='STK'
            c.exchange ='SMART'
            c.currency ='USD'
            cList.append(c)
            ibApp.reqContractDetails(3, c)
        pass

    '''
    scSub = scanner.ScannerSubscription()
    scSub.numberOfRows = 80
    scSub.instrument = 'STK'
    scSub.locationCode = 'STK.US.MAJOR'
    scSub.scanCode = 'OPT_VOLUME_MOST_ACTIVE'
    scSub.belowPrice = 5
    ibApp.reqScannerSubscription(31,scSub,[], [])
    '''
    #ibApp.reqScannerParameters()
    #time.sleep(10); ibApp.disconnect(); sys.exit(0)

    c  = contract.Contract()
    c.symbol ='SPY' if len(sys.argv) ==1 else sys.argv[1]
    c.secType ='STK'
    c.exchange ='SMART'
    c.exchange ='CBOE'
    c.currency ='USD'

    ibApp.reqContractDetails(3, c)
    time.sleep(3)
    while 'contract' not in ibApp.d_:
        time.sleep(1)
    conId = ibApp.d_['contract'].conId
    #ibApp.reqHistoricalNews(10003, conId, "BRFG", "2020-05-21 00:00:00.0", "", 10, [])
    #ibApp.reqHistoricalNews(10003, conId, "BRFG+BRFUPDN+DJNL", "", "", 10, [])
    ibApp.reqHistoricalNews(10003, conId, "BZ+BRFG+BRFUPDN+DJNL", "2020-05-21 00:00:00.0", "", 130, [])
    ibApp.reqNewsProviders()
    time.sleep(5); ibApp.disconnect(); sys.exit(0)

    ibApp.reqHistoricalData(12, c, '', '2 D', '1 hour', 'TRADES',useRTH=0,formatDate=1,keepUpToDate=False, chartOptions=[])
    time.sleep(3)
    # Obtain the server time via the IB API app
    server_time = ibApp.obtain_server_time()
    server_time_readable = datetime.datetime.utcfromtimestamp(
        server_time
    ).strftime('%Y-%m-%d %H:%M:%S')
    print("Current IB server time: %s" % server_time_readable)
    ibApp.disconnect()
    sys.exit(0)
    import  doctest
    doctest.testmod();
