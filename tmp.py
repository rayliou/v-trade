#!/usr/bin/env python3
# coding=utf-8
#from futu import *
from IPython.display import display, HTML
#import talib


from datasource.ib import IBKR
import glob
import pandas as pd
import time
from datetime import datetime
ibkr = IBKR


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

files = glob.glob('20211229.*.Yahoo.test/lineregress*.csv')
print(files)
dfs = [ pd.read_csv(f) for f in files]
df0  = pd.concat(dfs)
#time.sleep(2)
df = pd.DataFrame(df0)
df = fillMktPrice(df,['n1', 'n2'])
display(df)
#print(datetime.now().strftime('%H:%M:%S'))
#print()
