#!/usr/bin/env python3
# coding=utf-8
#from futu import *
from IPython.display import display, HTML
#import talib
import yfinance as yf
#import numpy as np
#import pandas as pd
#import matplotlib.pyplot as plt
#from datetime import datetime
#from datetime import timedelta
from pyhocon import ConfigFactory
from datetime import datetime
import os.path,os,sys,time
import glob,re
import hashlib
import logging,json
from Log import logInit
import pandas as pd

from DataDownloadFutu import DataDownloadFutu
from gw.GwIB import GwIB
from gw.HistoricalDataLimitations import HistoricalDataLimitations



'''
- HK https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
- US https://github.com/ranaroussi/yfinance/
-    https://aroussi.com/post/python-yahoo-finance
'''


class SyncHistoryToLocal:
    log = logging.getLogger("main.SyncHistoryToLocal")
    SHARDED_NUM = 20
    SEQ_START   = 1000
    def __init__(self, confPath='./conf/v-trade.utest.conf'):
        #self.confPath_ = 'conf/v-trade.conf'
        self.confPath_ = confPath
        self.c_ = ConfigFactory.parse_file(self.confPath_)
        self.dataRoot_ =  self.c_ .data.rootDir
        assert self.dataRoot_ is not None and self.dataRoot_ != ''
        self.limitation_ = HistoricalDataLimitations(self.c_)

        pass
    def run(self, gwSource):
        #rebuild or init data dir
        self.initDataDir()
        s = 'AAPL'
        d = self.getStockDir('us',s)
        exist = os.path.isdir(d)
        self.log.debug(f'{s} -> {d}, exist:{exist}')
        for market in stocks:
            for k,v in self.getParallelGroups(market).items():
                if  k == '':
                    pass
                else:
                    pass
                # 1st Fetch data from the last day to today
                start,end  = None,None
                self.fetchData(start,end)
                #wait according to the speed limit

                # then. Fetch the data that is  before the earliest day in local files
                self.fetchData(start,end)
                #wait according to the speed limit
                pass
        pass

    def fetchData(self, startDate,endDate):
        self.limitation_.wait()
        self.limitation_.logCall()
        pass
    def getParallelGroups(self,market, symbols = []):
        '''
        >>> s  = SyncHistoryToLocal()
        >>> s.initDataDir()
        >>> dirAAPL = s.getStockDir('us','AAPL')
        >>> dirABNB = s.getStockDir('us','ABNB')
        >>> dirGOOGL = s.getStockDir('us','GOOGL')
        >>> dirBZ = s.getStockDir('us','BZ')
        >>> dirF = s.getStockDir('us','F')
        >>> dirS = s.getStockDir('us','S')
        >>> mDir = s.getStockDir('us')
        >>> import shutil; shutil.rmtree(mDir)
        >>> s.initDataDir()
        >>> existedFiles = [ '999-AAPL-20090702-20190805-5m.csv',\
                '998-GOOGL-20090702-20190805-5m.csv',\
                '1000-ABNB-20110702-20120805-5m.csv',\
                '1000-BZ-20110702-20120805-5m.csv', \
                '1000-F-20000702-20000905-5m.csv', ]
        >>> allFilesPath =  ' '.join([f'{s.getStockDir("us",f)}/{f}' for f in existedFiles])
        >>> cmd  = f'touch {allFilesPath}'; os.system(cmd)
        0
        >>> symbols = ['AAPL', 'ABNB','GOOGL','SPY', 'QQQ']
        >>> groups = s.getParallelGroups('us',symbols)
        >>> groups
        {'': ['SPY', 'QQQ'], '20110702-20120805': [['1000', 'ABNB', '20110702', '20120805', '5m.csv'], ['1000', 'BZ', '20110702', '20120805', '5m.csv']], '20090702-20190805': [['998', 'GOOGL', '20090702', '20190805', '5m.csv'], ['999', 'AAPL', '20090702', '20190805', '5m.csv']], '20000702-20000905': [['1000', 'F', '20000702', '20000905', '5m.csv']]}
        '''
        mDir = self.getStockDir(market)
        files = glob.glob(f'{mDir}/*/*.csv')
        files = [f.split('/')[-1] for f in files]
        groups =  {'':[]   }
        symsExisted = set()
        for f in files:
            parts = f.split('-')
            if len(parts) != 5:
                continue
            seq, sym, start,end, interval = parts
            symsExisted.add(sym)
            k = f'{start}-{end}'
            if not k in groups:
                groups[k] = []
            groups[k].append(parts)
        groups[''] = [s  for s in symbols if s not in symsExisted]
        return groups

    def initDataDir(self):
        if not os.path.isdir(self.dataRoot_):
            os.mkdir(self.dataRoot_)
        stocks = self.c_.ticker.stock
        for market in stocks:
            mDir = self.getStockDir(market)
            if not os.path.isdir(mDir):
                os.mkdir(mDir)
            for i in range(0,self.SHARDED_NUM):
                sDir = f'{mDir}/{i}'
                if not os.path.isdir(sDir):
                    os.mkdir(sDir)
                self.log.debug(f'{sDir} is initialized.')
        pass
    def getStockDir(self, market, symbol = None):
        '''
        symbol : None , return the parent dir of the symbol
        '''
        parent = f'{self.dataRoot_}/stock_{market}'
        if symbol is None:
            return parent
        #shards individual stock to diffrent dirs.
        sharded = int(hashlib.sha1(symbol.encode("utf-8")).hexdigest(), 16) % self.SHARDED_NUM
        sharded = abs(sharded)
        return f'{parent}/{sharded}'

    def mergeMSymbolsData(self, parentDir = './data.cn'):
        import glob
        ds  = glob.glob(f'{parentDir}/*.csv')
        symFiles  = dict()
        for d in ds:
            s = d.split('/')[-1].split('-')[0]
            if s not in symFiles:
                symFiles[s] = []
            symFiles[s].append(d)
        dfDict  = dict()
        for k,v in symFiles.items():
            v  = [ pd.read_csv(d,index_col=0,parse_dates=True) for d in v]
            df = pd.concat(v).sort_values(by='date')
            df.columns = pd.MultiIndex.from_product([[k],df.columns, ])
            dfDict[k]= df
        #merge close
        dfOut  = None
        for k,v in dfDict.items():
            if dfOut is None:
                dfOut = v
            else:
                #FIXME TODO use pandas.merge_ordered instead
                dfOut = pd.merge_asof(dfOut , v, right_index=True, left_index=True, suffixes=('','_x'))
        now  = datetime.now().strftime('%Y%m%d')
        hdPath  = f'{parentDir}/{now}.csvx'
        dfOut.to_csv(hdPath)
        self.log.debug(f'Write file {hdPath}')
        return dfOut

    def concatDataFiles(self, srcFileList ,dstFile):
        v  = [ pd.read_csv(f,index_col=0, header=[0,1], parse_dates=True) for f in srcFileList]
        df = pd.concat(v).sort_values(by='date').drop_duplicates()
        df.to_csv(dstFile)
        return df
    pass


if __name__ == '__main__':
    logInit()
    #import doctest; doctest.testmod(); sys.exit(0)
    s  = SyncHistoryToLocal()
    df = s.concatDataFiles(['data/20211223.csvx', './data.cn.20211222/20211222.csvx'], './xxx.csv') ; display(df); sys.exit(0)
    #df  = s.mergeMSymbolsData('./data.topus')
    df  = s.mergeMSymbolsData('./data')
    display(df)
    #s.run()
    sys.exit(0)
