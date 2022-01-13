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


def load_merged_data(file = 'data.cn/20211222.csvx'):
    msg  = f'pd.read_csv({file}, index_col=0, header=[0,1], parse_dates=True )'
    print(msg)
    df  = pd.read_csv(file, index_col=0, header=[0,1], parse_dates=True )
    df = df[ ~ df.isna().any(axis=1)]
    #symbols = ','.join(set([c[0] for c in df.columns]))
    symbols = list(set([c[0] for c in df.columns]))
    return df,symbols

class OLS:
    log = logging.getLogger("main.OLS")
    def __init__(self,df, symbols, maxDays =30):
        self.df_ = df
        self.symbols_ = symbols
        self.maxDays_ = maxDays
        start = datetime.now() - timedelta(days=self.maxDays_)
        self.df_ = self.df_ [self.df_.index >start]
        display(self.df_.head(1))
        display(self.df_.tail(1))
        self.log.debug(f'symbols:{",".join(self.symbols_)}')
        pass
    def run(self):
        symList = self.symbols_
        N = len(self.symbols_)
        P = np.zeros((N,N))
        P  = pd.DataFrame(P)
        P.index = P.columns = symList
        #loop
        pPairs = []
        cnt  = 0
        totalCnt =  int(N *(N-1) /2)
        for i in range(N):
            for j in range(i+1,N):
                k1 = symList[i]
                k2 = symList[j]
                cnt += 1
                X1 = self.df_[k1].close
                X2 = self.df_[k2].close
                _, pCoin, _ = coint(X1, X2)
                self.log.debug(f'[{cnt}/{totalCnt}]:\t{k1} {k2}\t{pCoin}')
                v = {'pair': f'{k1}_{k2}', 'p': pCoin}
                v['n1'] = k1
                v['n2'] = k2
                pPairs.append(v)
                #P[k1][k2] = P[k2][k1] = pCoin
        #display(P.SPY.sort_values())
        dfPairs = pd.DataFrame(pPairs)
        dfPairs = dfPairs[dfPairs.p <= 0.05].sort_values(by='p')
        dfPairs.set_index('pair', inplace=True)
        return dfPairs
        #dfPairs.to_csv(self.coinPath_, index=False)
    pass

@click.command()
@click.argument('bigcsv')
@click.argument('dst')
@click.option('-d','--max_days',  help='', default=30)
@click.option('--stock_plates_json',  help='', default='')
def ols(bigcsv,dst,max_days, stock_plates_json):
    logInit()
    df,symbols = load_merged_data(bigcsv)
    c  = OLS(df,symbols,max_days)
    dfP = c.run()
    if stock_plates_json != '':
        extList = []
        StockWithPlates.read_json_file(stock_plates_json)
        for idx,r in dfP.iterrows():
            ext = ''
            setN1,setN2 =  set(),set()
            if r.n1 in StockWithPlates.stocks:
                ext += StockWithPlates.stocks[r.n1].stock_name_
                setN1 =  set(StockWithPlates.stocks[r.n1].plates_.keys())
            ext += '-'
            if r.n2 in StockWithPlates.stocks:
                ext += StockWithPlates.stocks[r.n2].stock_name_
                setN2 =  set(StockWithPlates.stocks[r.n2].plates_.keys())
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

    cli(); sys.exit(0)

