#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''


import math,sys
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
from statsmodels.tsa.stattools import coint
from statsmodels.tsa.stattools import adfuller

import pandas as pd
import numpy as np
import seaborn as sns
from scipy.stats import norm
from scipy import stats
from IPython.display import display, HTML
import yfinance as yf
from datetime import datetime
from Log import logInit

from History import HistoryYahoo, HistoryFutu


def getRatios( var1, var2,df, plotOrNot=False):
    df1 = df[[var1, var2]].dropna()
    S1 = df1[var1]
    S2 = df1[var2]
    ratios = S1 / S2
    if plotOrNot:
        plt.figure(figsize=(10,5))
        ratios.hist(bins = 200)
        plt.title("Ratios histogram")
        plt.ylabel('Frequency')
        plt.xlabel('Intervals')
        plt.show()
    return S1, S2, ratios


class Hedge:
    def __init__(self,days=58, interval='5m', isHK = False):
        self.isHK_ = isHK
        self.maxDays5m = 59
        self.maxDays1h = 729
        if self.isHK_:
            self.maxDays5m = 365 * 1
            self.maxDays1h = 365 * 2
        self.days_ = days
        self.interval_ = interval
        if self.interval_ == '5m':
            self.days_ = days if days < self.maxDays5m else self.maxDays5m
        if self.interval_ == '1h':
            self.days_ = days if days < self.maxDays1h else self.maxDays1h
        self.h_ = HistoryYahoo()
        pass

    def mDownload(self,symbols):
        symList = symbols.replace(',',' ').split()
        df  = self.h_.mdownload(symbols,days=self.days_, interval=self.interval_ )
        dfO  = dict()
        for s in symList:
            dfO[s] = df[s].Close
        dfO  = pd.DataFrame(dfO)
        dfO.fillna(method='bfill', inplace=True)
        return dfO

    def mCointegration(self,symbols, showTopPairs = True, showTopSymsForEach = False, doPlot=False):
        dfO  = self.mDownload(symbols)
        symList = symbols.replace(',',' ').split()
        N = len(symList)
        P = np.zeros((N,N))
        P  = pd.DataFrame(P)
        P.index = P.columns = symList
        #loop
        pPairs = []
        for k1 in symList:
            for k2 in symList:
                if k2 == k1:
                    P[k1][k1] =0.0
                    break
                X1 = dfO[k1]
                X2 = dfO[k2]
                _, pCoin, _ = coint(X1, X2)
                P[k1][k2] = P[k2][k1] = pCoin
                v = {'n1': k1, 'n2':k2, 'p': pCoin}
                pPairs.append(v)
        #display(P.SPY.sort_values())
        pPairs = pd.DataFrame(pPairs)
        pPairs = pPairs[pPairs.p <= 0.1].sort_values(by='p')
        now  = datetime.now().strftime('%Y%m%d')
        if showTopPairs:
            pPairs.to_csv(f'Top-paris-{now}.csv', index=False)
            display( pPairs)
        if showTopSymsForEach:
            for c in P:
                p =  P[c]
                sOut = ','.join(
                    [f'{k}:{v},' for k,v in p[p < 0.1].sort_values().items()]
                )
                print(f'{c}:{sOut}')
                pass

        if doPlot:
            fig = plt.figure(figsize = (12,8))
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
            ax1 = fig.add_subplot(111)
            sns.heatmap(P,ax=ax1)
            plt.show()
        return P

    def testCointegration(self,x,y,data):
        X1 = data[x]
        X2 = data[y]
        _, pCoin, _ = coint(X1, X2)
        corr, pCorr = pearsonr(X1,X2)
        #gtest Stationarity
        pStationarityX1 = adfuller(X1)[1]
        pStationarityX2 = adfuller(X2)[1]
        print(f'pStationarityX1:{pStationarityX1:.4f};pStationarityX2:{pStationarityX2:.4f};pCoin:{pCoin:.8f},corr:{corr:.4f},pCorr:{pCorr:.4f} ')
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

    def testLinregress(self,symbols ='AMZN,JPM', ax = None):
        '''
        TODO 解决未来函数问题

        '''
        symList = symbols.replace(',',' ').split()
        x,y = symList[0], symList[1]
        df  = self.mDownload(symbols)
        totalN = df.shape[0]
        outList = self.rollingLinregress(x,y,df)
        lineRegN = len(outList)

        out = { 'intercept' : np.nan, 'slope' : np.nan}
        outList2 =  [out] *(totalN -lineRegN) + outList
        dfLR = pd.DataFrame(outList2)
        dfLR.index = df.index
        df['intercept'] = dfLR.intercept
        df['slope'] = dfLR.slope
        display(df)

        diff  = df.intercept + df.slope* df[x] - df[y]
        display(diff)
        df['diff'] = diff
        if ax is  None:
            fig = plt.figure(figsize = (12,8))
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
            ax = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)

            df[[x]].plot(ax=ax2)
            df[[y]].plot(ax=ax2,secondary_y=True)

            df[['diff']].plot(ax=ax)
            mean = df['diff'].mean()
            std = df['diff'].std()
            ax.axhline(mean-std*2, color='r', linestyle='--', label= f'Buy {x}/Sell {y}')
            ax.axhline(mean+std*2, color='g', linestyle='--', label= f'Sell {x}/Buy {y}')
            ax.axhline(mean-std, color='y', linestyle='--')
            ax.axhline(mean+std, color='y', linestyle='--')
            ax.axhline(mean,  linestyle='--')
            ax.set_title(f'+:{x} short {x}+ long {y};-:short {y}+ long {x};')
            plt.legend()
            plt.show()
        pass

    def linregress(self,X,Y,out):
        '''
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html
        '''
        res = stats.linregress(X, Y)
        #print(f"Intercept={res.intercept};slope={res.slope};  R-squared: {res.rvalue**2:.6f}")
        #ax.plot(x, res.intercept + res.slope*x, 'r+', label='lllll')
        out['intercept'] = res.intercept
        out['slope'] = res.slope
        return 1

    def rollingLinregress(self,x,y,data, window=780):
        outList = []
        self.rollingAuxFunc(x,y,data,outList,window, self.linregress)
        return  outList

    def rollingAuxFunc(self,x,y,data,outList, window,  rollFunc):
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
            out  = dict()
            ret = rollFunc(Xwin,Ywin,out)
            outList.append(out)
            return ret
        #print(f'dsAux={dsAux}')
        dsAux.rolling(window=window ,min_periods=100).apply(auxWindowFunc,raw=True)
        pass


    def corrAnalysis(self,symbols):
        symListStr = 'LLY,DHR,ADBE,AVGO,COST,TMO,ACN,LOW,INTU,CVX,WFC,PFE,AMZN,AMD,ABNB,XOM,JPM,BAC,UNH,HD,TSLA,NVDA,AAPL,GOOGL,MSFT,QQQ,SPY'
        self. mCointegration(symListStr)
        plt.show()
        pass

    pass



if __name__ == '__main__':
    logInit()
    syms = sys.argv[1] if len(sys.argv) >1 else  'AMZN,JPM'
    days,interval = 58,'5m'
    h = Hedge(days=days, interval=interval)
    h.testLinregress(syms); sys.exit(0)
    h.corrAnalysis(syms); sys.exit(0)


    sys.exit(0)
