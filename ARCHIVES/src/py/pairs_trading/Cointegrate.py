#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''

#from scipy.stats import pearsonr, spearmanr
from statsmodels.tsa.stattools import coint
#from statsmodels.tsa.stattools import adfuller

import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime, timedelta
import sys,time,inspect,os
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
#sys.path.insert(0, f'../{parentdir}')
#sys.path.insert(0, parentdir)
from Log import logInit
from pyhocon import ConfigFactory
import hashlib,json
import click,logging
from screener.ScreenByPlates import StockWithPlates

from common.BigPandasTable import load_merged_data

class Cointegrate:
    MIN_DAYS = 14
    MAX_TIMES = 3
    log = logging.getLogger("main.Cointegrate")
    def __init__(self,df, symbols, end_date=''):
        #set model date.
        self.end_date_ = end_date
        df =  df[:end_date] if end_date is not None and end_date != '' else df
        start = df.index[-1] - timedelta(days=self.MIN_DAYS * self.MAX_TIMES)
        df =  df[start:]

        self.symbols_ = symbols
        self.pThreshhold_ = 0.06
        self.df_ =  df
        display(self.df_.head(1))
        display(self.df_.tail(1))
        self.log.debug(f'symbols:{",".join(self.symbols_)}')
        pass
    def run(self):
        '''
        /Users/henry/stock/v-trade/data/data_study/stk-daily-20220125.cn.Yahoo.1m.csv
        2021-10-28 09:30:00 -> 2022-01-24 15:59:00
        '''
        symList = self.symbols_
        N = len(self.symbols_)
        P = np.zeros((N,N))
        P  = pd.DataFrame(P)
        P.index = P.columns = symList
        #loop
        pPairs = []
        cnt  = 0
        # start = datetime.now() - timedelta(days=int(self.maxDays_)/2)
        # start = df.index[-1] - timedelta(days=self.maxDays_)
        totalCnt =  int(N *(N-1) /2)
        for i in range(N):
            for j in range(i+1,N):
                k1 = symList[i]
                k2 = symList[j]
                v = {'pair': f'{k1}_{k2}', }
                cnt += 1
                pList = []
                pMin = 1.0
                start_of_pmin = None
                #14,28,42
                for dTimes in range(1,self.MAX_TIMES+1):
                    days=self.MIN_DAYS*dTimes
                    start = self.df_.index[-1] - timedelta(days=days)
                    X = self.df_[k1][start:].close
                    Y = self.df_[k2][start:].close
                    # self.log.info(f'coint(X:{X.index[0]}:{X.index[-1]};Y:{Y.index[0]}:{Y.index[-1]}) start:{start} ')
                    _, pCoin, _ = coint(X,Y)
                    v["p_"+ str(days)] = pCoin
                    pList.append(pCoin)
                    if pCoin < pMin:
                        pMin = pCoin
                        start_of_pmin = start
                    #display(X);sys.exit(0)
                p = np.mean(pList)                           
                v.update({'p': p, 'pmin':pMin, 'start_of_pmin':start_of_pmin,})
                self.log.debug(f'[{self.end_date_}]:[{cnt}/{totalCnt}]:\t{v}') 
                pPairs.append(v)
                #P[k1][k2] = P[k2][k1] = pCoin
        #display(P.SPY.sort_values())
        dfPairs = pd.DataFrame(pPairs)
        dfPairs = dfPairs.sort_values(by='p',ascending=True).head(100)
        dfPairs.set_index('pair', inplace=True)
        return dfPairs
        #dfPairs.to_csv(self.coinPath_, index=False)
    pass

@click.command()
@click.argument('bigcsv')
@click.argument('dst')
@click.option('--stock_plates_json',  help='', default='')
@click.option('--end_date',  help='', default='')
def cointegrate(bigcsv,dst,stock_plates_json, end_date):
    logInit()
    df,symbols = load_merged_data(bigcsv)
    c  = Cointegrate(df,symbols,end_date)
    dfP = c.run()
    #display(dfP)
    if stock_plates_json != '':
        extList = []
        StockWithPlates.read_json_file(stock_plates_json)
        for idx,r in dfP.iterrows():
            ext = ''
            setN1,setN2 =  set(),set()
            n1,n2 = idx.split('_')
            if n1 in StockWithPlates.stocks:
                ext += StockWithPlates.stocks[n1].stock_name_
                setN1 =  set(StockWithPlates.stocks[n1].plates_.keys())
            ext += '-'
            if n2 in StockWithPlates.stocks:
                ext += StockWithPlates.stocks[n2].stock_name_
                setN2 =  set(StockWithPlates.stocks[n2].plates_.keys())
            ext += '-'
            setBoth = setN1.intersection(setN2)
            plates = [StockWithPlates.plateCodeToCnName[p]  for p in setBoth]
            ext +=  ','.join(plates)
            extList.append(ext)
        #TODO BUG dfP['ext'] = pd.Series(extList)
        dfP['ext'] = extList
    display(dfP)
    dfP.to_csv(dst)
    c.log.debug(f'Wrote {dst}')

    pass


@click.group()
def cli():
    pass


if __name__ == '__main__':

    cli.add_command(cointegrate)
    cli(); sys.exit(0)
