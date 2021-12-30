#!/usr/bin/env python3

# coding=utf-8
#from futu import *
from IPython.display import display, HTML
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


def fillMktPrice(df, symCols:list):
    slist = pd.concat([df[s] for s in symCols ])
    symList = ' '.join(set(slist))
    ibkr = IBKR()
    dfR  = ibkr.reqMktData(symList)[['markPrice','close']]
    for s in symCols:
        df  = df.join(dfR, on=s)
        df['x_'+s] = df.markPrice
        df.drop(['markPrice', 'close'], axis=1,inplace=True)
    d = df.x_n1 * df.slope + df.i - df.x_n2 - df.m
    df['d'] = d
    df['y/x']    = 1/df.slope
    df['z']    = d/df['std']
    #df.drop(['x', 'y'], axis=1,inplace=True)
    df = df[df.slope > 0]
    THRESHOLD =1.8
    df = df[(df.z > THRESHOLD) | (df.z <-THRESHOLD)].sort_values(by='std/Y(%)')
    return df
    pass

#df = fillMktPrice(df,['n1', 'n2'])

#display(df)

@click.command()
@click.argument('lrfiles', type=click.Path(exists=True), nargs=-1)
@click.option('--market',  help='us|hk', default='hk')
#def updatePairsSnapshot(pairsLregFiles, marker):
def updatePairsSnapshot(lrfiles,market):
    print(lrfiles)

    confPath = './conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)

    #files = glob.glob('20211228*/lineregress*.csv')
    dfs = [ pd.read_csv(f) for f in lrfiles]
    df  = pd.concat(dfs)
    symbList  = list(set(df.n1).union(set(df.n2)))
    contractDict = None
    gw = GwFutu(c) if market == 'hk' else GwIB(c)
    while True:
        time.sleep(2)
        if market == 'hk':
            dfPrice  = gw.getSnapshot(symbList)[['code','last_price']]
            dfPrice.set_index('code', inplace=True)
            dfPrice.rename('last_price', 'price',inplace=True)
        else:
            dfPrice,contractDict  = gw.getSnapshot(symbList, contractDict)
        for s in ['n1','n2']:
            df  = df.join(dfPrice, on=s)
            df['x_'+s] = df.price
            df.drop(['price',], axis=1,inplace=True)
        d = df.x_n1 * df.slope + df.i - df.x_n2 - df.m
        df['d'] = d
        df['y/x']    = 1/df.slope
        df['z']    = d/df['std']
        #df.drop(['x', 'y'], axis=1,inplace=True)
        df = df[df.slope > 0]
        THRESHOLD =1.8
        df = df[(df.z > THRESHOLD) | (df.z <-THRESHOLD)].sort_values(by='std/Y(%)')
        display(df)
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
    logInit(logging.ERROR)

    cli.add_command(updatePairsSnapshot)
    cli.add_command(test)
    cli()
    sys.exit(0)
