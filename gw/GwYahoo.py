#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *

import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime,timedelta,date
import matplotlib.pyplot as plt
import logging
import yfinance as yf

import threading,queue

from pyhocon import ConfigFactory

import sys,time,inspect,os
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit
from gw.BaseGateway import BaseGateway
from gw.HistoricalDataLimitations import HistoricalDataLimitations

import click


class GwYahoo(BaseGateway):
    log = logging.getLogger("main.GwYahoo")

    def __init__(self,config):
        BaseGateway.__init__(self,config)
        self.source_ = 'Yahoo'
        pass


    def mdownload(self,symbols, dst, interval):
        start,end = self.daysToStartEnd(59)
        self.dfBigTableHist_ = yf.download( tickers = symbols, start = start, end = end,
                interval = interval, group_by = 'ticker', auto_adjust = True, prepost = False , threads = True)
        self.rmtz()
        self.adjustColumns()
        self.dfBigTableHist_.to_csv(dst)
        pass

        pass
    def adjustColumns(self):
        df = self.dfBigTableHist_
        level0 = df.columns.get_level_values(0)
        N = int(len(level0)/5)
        level1 = ['open', 'high','low','close' , 'volume'] * N
        level = [level0, level1]
        t = list(zip(*level))
        self.dfBigTableHist_.columns = pd.MultiIndex.from_tuples(t)
        pass
    def rmtz(self):
        df = self.dfBigTableHist_
        self.dfBigTableHist_.index = self.dfBigTableHist_.index.tz_localize(None)
        #self.dfBigTableHist_.index = pd.to_datetime(df.index.str.replace('-[^-]+$','',regex=True))
        pass

    def daysToStartEnd(self, days):
        now = datetime.now()
        start = now - timedelta(days=days)
        start = start.strftime('%Y-%m-%d')
        end = (now +timedelta(days=1)) .strftime('%Y-%m-%d')
        return start,end
    pass

@click.command()
@click.option('--src',  help='src')
@click.option('--dst',  help='dst')
def rmtz(src,dst):
    assert src != dst
    df = pd.read_csv(src,index_col=0, header=[0,1], parse_dates=False)
    df.index = pd.to_datetime(df.index.str.replace('-[^-]+$','',regex=True))
    df.to_csv(dst)
    pass

@click.command()
@click.argument('group')
@click.argument('dst')
@click.option('--interval',  help='5m,1m etc', default='5m')
def mdownload(group, dst, interval):
    confPath = '../conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)
    symbols = c.ticker.stock.us[group]
    symbols = ','.join(symbols)
    gw = GwYahoo(c)
    gw.mdownload(symbols,dst,interval)
    pass

@click.group()
def cli():
    pass


if __name__ == '__main__':
    logInit()
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        import doctest; doctest.testmod(); sys.exit(0)

    confPath = '../conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)
    gw = GwYahoo(c)
    cli.add_command(rmtz)
    cli.add_command(mdownload)
    cli()
    sys.exit(0)
