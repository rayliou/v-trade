#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
'''


import math,sys
import matplotlib.pyplot as plt
import seaborn as sns

import pandas as pd
import numpy as np
import seaborn as sns
from scipy.stats import norm
from scipy import stats
from IPython.display import display, HTML
import yfinance as yf
from Log import logInit

from History import HistoryYahoo, HistoryFutu

class Hedge:
    def __init__(self,isHK = False):
        self.isHK_ = isHK
        self.maxDays5m = 59
        self.maxDays5m = 53
        self.maxDays1h = 729
        if self.isHK_:
            self.maxDays5m = 365 * 1
            self.maxDays1h = 365 * 2
        self.h_ = HistoryYahoo()
        pass

    def rollingCorr(self,x,y,data,ax, window=15):
        X = data[x]
        Y = data[y]
        N = X.index.size
        dsAux = pd.Series(np.arange(N)) #value
        dsAux.index  = X.index

        def auxWindowFunc(A):
            #print(f'A={A}')
            b = int(A[0])
            e = int(A[-1])
            Xwin = X[b:e]
            Ywin = Y[b:e]
            return Xwin.corr(Ywin)

        #print(f'dsAux={dsAux}')
        C = dsAux.rolling(window=window ,min_periods=window).apply(auxWindowFunc,raw=True)
        return C

    def linregress(self,x,y,data):
        '''
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html
        '''
        x = data[x]
        y = data[y]
        res = stats.linregress(x, y)
        print(f"Intercept={res.intercept};slope={res.slope};  R-squared: {res.rvalue**2:.6f}")
        #ax.plot(x, res.intercept + res.slope*x, 'r+', label='lllll')
        return res.intercept,res.slope
        pass

    def corrAnalysis(self,symbols,interval ='5m',isHK = False):
        #symListStr = 'LLY,DHR,ADBE,AVGO,COST,TMO,ACN,LOW,INTU,CVX,WFC,PFE,AMZN,BRK.B,AMD,ABNB,XOM,JPM,BAC,UNH,HD,TSLA,NVDA,AAPL,GOOGL,MSFT'
        #symListStr = 'NVDA,AMD,QQQ,SPY,COST,HD'
        sPair = symbols.replace(',',' ').split()
        assert len(sPair)  == 2
        x = sPair[0]
        y = sPair[1]

        symListStr = f'{x},{y}'
        symList = symListStr.replace(',',' ').split()
        days  = self.maxDays1h if interval == '1h' else self.maxDays5m
        #interval,days = '1d',365*2
        print(f'Call mdownload({symListStr},days={days}, interval={interval}' )
        df  = self.h_.mdownload(symListStr,days=days, interval=interval )
        dfO  = dict()
        for s in symList:
            dfO[s] = df[s].Close
        dfO  = pd.DataFrame(dfO)
        dfO  = dfO /dfO.shift(1) -1
        dfO = dfO.fillna(0.0001)

        fig = plt.figure(figsize = (12,8))
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        sns.regplot(x=x, y=y, data=dfO, x_jitter=.05,ax=ax1);
        #sns.scatterplot(x=x, y=y,  data=dfO,ax=ax2);
        dfO['rollCorr'] = self.rollingCorr(x,y,dfO,ax=ax2,window=24)
        self.linregress(x,y,data=dfO)
        dfO[[x,y]].plot(ax=ax2)
        dfO[['rollCorr']].plot(ax=ax2,secondary_y=True)
        #ax3 = fig.add_subplot(313)

        #sns.lmplot(x="AMD", y="NVDA", data=dfO, x_jitter=.05,ax=ax1);
        #sns.relplot(x="AMD", y="NVDA",  data=dfO,ax=ax2);


        '''
        ax = sns.heatmap(dfO.corr(),ax=ax)
        '''
        plt.show()
        pass

    def downloadHistories(self,symbols,interval ='5m',isHK = False):
        sPair = symbols.replace(',',' ').split()
        assert len(sPair)  == 2
        assert interval == '5m' or interval == '1h'
        days  = self.maxDays1h if interval == '1h' else self.maxDays5m
        df  = self.h_.mdownload(symbols,days=days, interval=interval )
        dsA = (df[sPair[0]].Close)
        dsB = (df[sPair[1]].Close)

        display(df[sPair[0]].Close)
        display(df[sPair[1]].Close)
        print(f'Correlation between {sPair[0]} and {sPair[1]} = {dsA.corr(dsB)}')
        pass
    pass



if __name__ == '__main__':
    logInit()
    h = Hedge()
    syms = sys.argv[1] if len(sys.argv) >1 else  'AMD,NVDA'
    h.corrAnalysis(syms); sys.exit(0)
    h.downloadHistories(syms,'5m')
    sys.exit(0)
