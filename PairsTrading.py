#!/usr/bin/env python3

# coding=utf-8
#from futu import *
from IPython.display import display, HTML
from numpy import disp
#import talib


from datasource.ib import IBKR
import glob,sys,time,datetime
import pandas as pd
ibkr = IBKR

from gw.GwFutu import GwFutu
from gw.GwIB import GwIB

import click
import logging
from Log import logInit
from pyhocon import ConfigFactory


#df = fillMktPrice(df,['n1', 'n2'])

#display(df)

@click.command()
@click.argument('lrfiles', type=click.Path(exists=True), nargs=-1)
@click.option('--market',  help='us|hk', default='hk')
#def updatePairsSnapshot(pairsLregFiles, marker):
def updatePairsSnapshot(lrfiles,market):
    pd.options.display.max_colwidth = 200
    print(lrfiles)

    confPath = './conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)

    #files = glob.glob('20211228*/lineregress*.csv')
    dfs = [ pd.read_csv(f) for f in lrfiles]
    df  = pd.concat(dfs)
    symbList  = list(set(df.n1).union(set(df.n2)))
    cdsList = None
    gw = GwFutu(c) if market == 'hk' else GwIB(c)
    while True:
        time.sleep(1)
        if market == 'hk':
            dfPrice  = gw.getSnapshot(symbList)[['code','last_price']]
            dfPrice.set_index('code', inplace=True)
            dfPrice.rename('last_price', 'price',inplace=True)
        else:
            dfPrice,cdsList  = gw.getSnapshot(symbList, cdsList)
        for s in ['n1','n2']:
            df  = df.join(dfPrice, on=s, how='inner')
            df['BID_'+s] = df.BID
            df['ASK_'+s] = df.ASK
            df['LAST_'+s] = df.LAST
            df['CLOSE_'+s] = df.CLOSE
            df.drop(['BID','ASK','CLOSE','LAST' ], axis=1,inplace=True)
        #n1 > n2
        d1 = df.BID_n1 * df.slope + df.i - df.ASK_n2 - df.m
        #n1 < n2
        d2 = df.ASK_n1 * df.slope + df.i - df.BID_n2 - df.m
        #display(df)
        df['z1(-n1+n2)']    = d1/df['std']
        df['n1_n2']    = df.n1 +'_' + df.n2
        df['z2(+n1-n2)']    = d2/df['std']
        df['y/x']    = 1/df.slope
        #df.drop(['x', 'y'], axis=1,inplace=True)
        df = df[df.slope > 0]
        THRESHOLD =1.9
        df = df[(df['z1(-n1+n2)'] > THRESHOLD) | (df['z2(+n1-n2)'] <-THRESHOLD)].sort_values(by='std/Y(%)').tail(50)
        df['arg']  = df.n1 + ' ' +  df.n2 + ' -s ' + df.slope.map(str) + ' -m ' + df.m.map(str) + ' --std ' + df['std'].map(str) + ' -i ' + df.i.map(str)

        display(df[['std/Y(%)', 'BID_n1', 'ASK_n1', 'LAST_n1', 'CLOSE_n1', 'BID_n2', 'ASK_n2', 'LAST_n2', 'CLOSE_n2', 'z1(-n1+n2)', 'n1_n2', 'z2(+n1-n2)', 'y/x', 'arg', ]  ],raw=True)
        print(datetime.datetime.now().strftime('%H:%M:%S'))

    sys.exit(0)
    pass


@click.command()
def test():
    import doctest; doctest.testmod();
    sys.exit(0)
    pass

@click.group()
def cli():
    pass

if __name__ == '__main__':
    #logInit()
    logInit(logging.ERROR)

    cli.add_command(updatePairsSnapshot)
    cli.add_command(test)
    cli()
    sys.exit(0)