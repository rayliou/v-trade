#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''


import math,sys,os.path
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
from datetime import datetime, timedelta
from Log import logInit
from pyhocon import ConfigFactory
import hashlib

from History import HistoryYahoo, HistoryFutu


def load_merged_data(file = 'data.cn/20211222.csvx'):
    msg  = f'pd.read_csv({file}, index_col=0, header=[0,1], parse_dates=True )'
    print(msg)
    df  = pd.read_csv(file, index_col=0, header=[0,1], parse_dates=True )
    df = df[ ~ df.isna().any(axis=1)]
    symbols = ','.join(set([c[0] for c in df.columns]))
    return df,symbols

class Hedge:
    def __init__(self, bigTableFile, maxDays =60, lRegWindow = 500 ):
        self.bigTableFile_ = bigTableFile
        self.maxDays_ = maxDays
        self.lRegWindow_ = lRegWindow
        self.bigTableDir_ = os.path.dirname(self.bigTableFile_)
        self.df_ ,self.symbols_ = load_merged_data(self.bigTableFile_)
        start = datetime.now() - timedelta(days=maxDays)
        self.df_ = self.df_ [self.df_.index >start]

        display(self.df_.head(2))
        display(self.df_.tail(2))
        today  = datetime.now().strftime('%Y%m%d')
        self.TopConinPairsFile_ =  f'{self.bigTableDir_}/top-pairs-{today}.csv'
        self.TopZScoreFile_ =  f'{self.bigTableDir_}/top-pairs-z-{today}.csv'

        pass


    def mCointegration(self):
        symList = self.symbols_.replace(',',' ').split()
        N = len(symList)
        P = np.zeros((N,N))
        P  = pd.DataFrame(P)
        P.index = P.columns = symList
        #loop
        pPairs = []
        cnt  = 0
        totalCnt =  int(N *(N-1) /2)
        for k1 in symList:
            for k2 in symList:
                cnt += 1
                if k2 == k1:
                    P[k1][k1] =0.0
                    break
                X1 = self.df_[k1].close
                X2 = self.df_[k2].close
                _, pCoin, _ = coint(X1, X2)
                print(f'[{cnt}/{totalCnt}]:\t{k1} {k2}\t{pCoin}')
                P[k1][k2] = P[k2][k1] = pCoin
                v = {'n1': k1, 'n2':k2, 'p': pCoin}
                pPairs.append(v)
        #display(P.SPY.sort_values())
        pPairs = pd.DataFrame(pPairs)
        pPairs = pPairs[pPairs.p <= 0.05].sort_values(by='p')
        pPairs.to_csv(self.TopConinPairsFile_, index=False)
        display( pPairs)
        # fig = plt.figure(figsize = (12,8))
        # plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        # ax1 = fig.add_subplot(111)
        # sns.heatmap(P,ax=ax1)
        # plt.show()
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

    def rollingCorr(self,x,y,data,ax):
        X = data[x].close
        Y = data[y].close
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
        C = dsAux.rolling(window=self.lRegWindow_ ,min_periods=self.lRegWindow_).apply(auxWindowFunc,raw=True)
        return C

    def mTestLinregress(self):
        dfPairs= pd.read_csv(self.TopConinPairsFile_)
        oList = []
        cnt = 1
        totalN = dfPairs.shape[0]
        for index,row in dfPairs.iterrows():
            x = row.n1
            y = row.n2
            print(f'{cnt}/{totalN}t:\t', end='')
            o = self.testLinregress(f'{x},{y}')
            oList.append(o)
            cnt  += 1
        dfZ = pd.DataFrame(oList)
        dfPairs = pd.concat([dfPairs,dfZ],axis=1)
        r = dfPairs['std']/dfPairs['y']
        dfPairs['std/Y(%)'] = r * 100
        display(dfPairs)
        df = dfPairs[(dfPairs.z > 1.9) | (dfPairs.z < -1.9)].sort_values(by='z')
        df.to_csv(self.TopZScoreFile_, index=False)
        display(df)
        pass

    def testLinregress(self,symbols ='AMZN,JPM', doPlot = False):
        '''
        TODO 解决未来函数问题

        '''
        df = self.df_
        symList = symbols.replace(',',' ').split()
        x,y = symList[0], symList[1]
        totalN = df.shape[0]
        outList = self.rollingLinregress(x,y,df)
        lineRegN = len(outList)

        out = { 'intercept' : np.nan, 'slope' : np.nan}
        outList2 =  [out] *(totalN -lineRegN) + outList
        dfLR = pd.DataFrame(outList2)
        dfLR.index = df.index
        df['intercept'] = dfLR.intercept
        df['slope'] = dfLR.slope

        diff  = df.intercept + df.slope* df[x].close - df[y].close
        #display(diff)
        mean = diff.mean()
        std = diff.std()
        d = diff[-1]
        zScore  = (d - mean)/std
        slope = df.slope[-1]
        intercept = df.intercept[-1]
        #x is too high
        if d >  mean + 2*std:
            print(f'-{x} +{y},\tmean:{mean:.3f}, std:{std:.4f}, slope:{slope:.4f}, intercept:{intercept:.4f} ')
        elif d <  mean - 2*std:
            print(f'+{x} -{y},\tmean:{mean:.3f}, std:{std:.4f} , slope:{slope:.4f}, intercept:{intercept:.4f} ')
        else:
            #print(f'*{x} *{y},\tmean:{mean:.3f}, std:{std:.4f} , slope:{slope:.4f}, intercept:{intercept:.4f} ')
            print('')
            pass

        df['diff'] = diff
        if doPlot :
            fig = plt.figure(figsize = (12,8))
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
            ax = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)

            df[[x]].plot(ax=ax2)
            df[[y]].plot(ax=ax2,secondary_y=True)

            df[['diff']].plot(ax=ax)
            ax.axhline(mean+std*2, color='g', linestyle='--', label= f'Sell {x}/Buy {y}')
            ax.axhline(mean-std*2, color='r', linestyle='--', label= f'Buy {x}/Sell {y}')
            ax.axhline(mean-std, color='y', linestyle='--')
            ax.axhline(mean+std, color='y', linestyle='--')
            ax.axhline(mean,  linestyle='--')
            ax.set_title(f'+:{x} short {x}+ long {y};-:short {y}+ long {x};')
            plt.legend()
            plt.show()
        return {'z':zScore, 'slope' :slope, 'm' :mean, 'std': std, 
        'x' : df[x].close[-1],'y' : df[y].close[-1]
        }

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
        X = data[x].close
        Y = data[y].close
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


    pass


if __name__ == '__main__':
    logInit()
    bigTablePath  = sys.argv[1]
    h = Hedge(bigTablePath, maxDays=90, lRegWindow=780)
    if len(sys.argv) <= 2:
        h.mCointegration()
    h.mTestLinregress(); sys.exit(0)


    sys.exit(0)
