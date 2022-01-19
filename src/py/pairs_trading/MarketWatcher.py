#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''

#from scipy.stats import pearsonr, spearmanr
from lib2to3.pygram import Symbols
import numpy as np
import matplotlib.pyplot as plt
#from numpy.core.fromnumeric import mean
from scipy import stats
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
#from statsmodels.tsa.stattools import adfuller

import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime, timedelta
import sys,time,inspect,os
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f'../{parentdir}')
sys.path.insert(0, parentdir)
from Log import logInit
from pyhocon import ConfigFactory
import hashlib,json
import click,logging
# from datetime import datetime,timedelta
import datetime

from common.BigPandasTable import load_merged_data
from gw.GwIB import GwIB

from common.BigPandasTable import load_merged_data

class MarketWatcher:
    log = logging.getLogger("main.MarketWatcher")
    def __init__(self,df, dfPairs,windowsize=800):
        pass
    pass

@click.command()
@click.argument('bigcsvs', type=click.Path(exists=True), nargs=-1)
@click.argument('dst')
@click.option('--conf',  help='conf file')
def snapshotsforbigcsvs(bigcsvs,dst,conf):
    '''
    ./MarketWatcher.py snapshotsforbigcsvs --conf ../../../conf/v-trade.utest.conf ../../../data/data_test/stk-merged-20220114.*.csv ../../../data/data_study/snapshotsforbigcsvs.20220114.csv
    '''
    print(f'(getallsnapshots{bigcsvs},{conf})')
    # pd.options.display.max_colwidth = 200
    c = ConfigFactory.parse_file(conf)
    logInit()
    symbols = set()
    for f in bigcsvs:
        df,s = load_merged_data(f)
        symbols.update(set(s))
    symbList  = list(symbols)
    cdsList = None
    gw = GwIB(c)
    print(f'Call gw.getSnapshot({symbList}, {cdsList})')
    dfPrice,cdsList  = gw.getSnapshot(symbList, cdsList)
    display(dfPrice)
    dfPrice.to_csv(dst, index=True)
    gw.log.debug(f'Wrote {dst}')
    gw.disconnect()
    pass


@click.command()
@click.argument('lrfiles', type=click.Path(exists=True), nargs=-1)
@click.option('--conf',  help='conf file')
@click.option('--threshold',  help='conf file', default=1.8)
def watchPairs(lrfiles,conf,threshold):
    print(f'watchPairs({lrfiles},{conf},{threshold}):')
    # pd.options.display.max_colwidth = 200
    c = ConfigFactory.parse_file(conf)
    dfs = [ pd.read_csv(f) for f in lrfiles]
    df  = pd.concat(dfs)
    symbList  = set()
    for s in [set(p) for p in df.pair.str.split('_')]:
        symbList.update(s)
    print( symbList)

    cdsList = None
    gw = GwIB(c)
    while True:
        dfPrice,cdsList  = gw.getSnapshot(symbList, cdsList)
        for s in ['n1','n2']:
            df  = df.join(dfPrice, on=s, how='inner')
            df['BID_'+s] = df.BID
            df['ASK_'+s] = df.ASK
            df['LAST_'+s] = df.LAST
            # df['CLOSE_'+s] = df.CLOSE
            df.drop(['BID','ASK','CLOSE','LAST' ], axis=1,inplace=True)
        #n1 > n2
        d1 = df.BID_n1 * df.s + df.i - df.ASK_n2 - df.m
        #n1 < n2
        d2 = df.ASK_n1 * df.s + df.i - df.BID_n2 - df.m
        df['z1(-n1+n2)']    = d1/df['st']
        df['z2(+n1-n2)']    = d2/df['st']
        df['y/x']    = 1/df.s
        df['st/price(%)']    = 100 * df.st/ np.maximum(df.LAST_n1,df.LAST_n2)

        df.drop(['BID_n1','ASK_n1','BID_n2','ASK_n2','LAST_n1','LAST_n2',   ], axis=1,inplace=True)
        #df.drop(['x', 'y'], axis=1,inplace=True)
        df = df[df.s > 0]
        df = df[(df['z1(-n1+n2)'] > threshold) | (df['z2(+n1-n2)'] <-threshold)].sort_values(by='st/price(%)').tail(50)
        df['arg']  = df.n1 + ' ' +  df.n2 + ' -s ' + df.s.map(str) + ' -m ' + df.m.map(str) + ' --st ' + df['st'].map(str) + ' -i ' + df.i.map(str)
        dfO = df[['pair','z1(-n1+n2)','z2(+n1-n2)','halflife', 'st/price(%)','y/x',  'arg', 'ext'] ]
        dfO.set_index('pair',inplace=True)
        display(dfO,raw=True)
        print(datetime.datetime.now().strftime('%H:%M:%S'))


    pass




@click.group()
def cli():
    pass


if __name__ == '__main__':
    cli.add_command(watchPairs)
    cli.add_command(snapshotsforbigcsvs)
    cli(); sys.exit(0)
