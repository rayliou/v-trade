#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
'''


import math,sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from scipy.stats import norm
from scipy import stats
from IPython.display import display, HTML
import yfinance as yf
from Log import logInit


def stdErr():
    m,s  = 2.0,1.5
    rvs = norm(m,s)
    X = rvs.rvs(size=20000)
    N = np.arange(20, 5000,10)
    def choice(N):
        S = np.random.choice(X,N)
        mS,sS  = S.mean(), S.std()
        sSN    = np.sqrt(((S - mS)**2).sum()/N)
        sSN1    = np.sqrt(((S - mS)**2).sum()/(N-1))
        return mS,sS,sSN,sSN1
    choice = np.frompyfunc(choice,1,4)
    mS,sS,sSN,sSN1 = choice(N)
    df  = pd.DataFrame({
        #'sSN1- sSN' :sSN1 -sSN
        #'mS' :mS
        's' :s
        ,'sSN1' :sSN1
        ,'sSN' :sSN
        }, index= N
        )
    fig = plt.figure(figsize = (12,8))
    ax = fig.add_subplot(211)  # 创建子图1
    df.plot(ax=ax)
    df['sSDiff'] = (sSN1 - sSN)/s
    df[['sSDiff']].plot(ax=ax,secondary_y=True)
    ax2 = fig.add_subplot(212)  # 创建子图1
    df.sSN1.hist(bins=100)
    plt.show()
    pass

def hv_Parksinson1980(o2,c2,h2,l2):
    N = o2.size
    k = (1/(4*N*math.log(2)))
    return math.sqrt (k* (np.log(h2/l2) ** 2).sum())

def hv_GarmaanKlass(o2,c2,h2,l2):
    c1 = c2.shift()
    N = o2.size
    sigma_sqare = (np.log(h2/l2) ** 2 /2 ).sum() /N - (2*math.log(2) -1  )*(np.log(c2/c1)**2).sum()/N
    sigma = math.sqrt(sigma_sqare) if sigma_sqare > 0 else 0
    #except ValueError as e:
    #    assert False , f'sigma_sqare={sigma_sqare}{e} '
    return sigma

def hv_YangZhang2000(o2,c2,h2,l2):
    #FIXME
    o1 = o2.shift()
    c1 = c2.shift()
    h1 = h2.shift()
    l1 = l2.shift()
    oLog  = np.log(o2/o1)
    cLog  = np.log(c2/c1)
    N = oLog.size
    sigma_o_square =  oLog.std() ** 2
    sigma_c_square =  cLog.std() ** 2
    sigma_rs_square =  (np.log(h2/c2)*np.log(h2/o2)+np.log(l2/c2)*np.log(l2/o2)).sum()/N
    k = 0.34/(1.34 +(N+1)/(N-1))
    #k = 0.34/(1. +(N+1)/(N-1))
    sigma  = np.sqrt(sigma_o_square  + k * sigma_c_square  + (1-k) * sigma_rs_square )
    return sigma

def hv_ewma(o2,c2,h2,l2):
    '''
    df  = pd.DataFrame()
    #df['std1_0.02'] = np.sqrt((np.log(c2/o2)**2).ewm(alpha=0.02,adjust=True).mean())
    df['std1_0.04'] = np.sqrt((np.log(c2/o2)**2).ewm(alpha=0.04,adjust=True).mean())
    df['std1_0.06'] = np.sqrt((np.log(c2/o2)**2).ewm(alpha=0.06,adjust=True).mean())
    df['std2'] = np.log(c2/o2).ewm(alpha=0.06,adjust=True).std()
    '''
    return np.log(c2/o2).ewm(alpha=0.06,adjust=True).std()[-1:][0]


from futu import *
from History import HistoryYahoo, HistoryFutu

g_hv_funcs = [
        hv_Parksinson1980,
        hv_GarmaanKlass,
        hv_YangZhang2000, #FIXME
        hv_ewma,
        ]




def t_interval2(code, isHK=False):
    hrsPerDay = 5.5 if isHK else 6.5
    interval = '5m'
    days = 59
    coeff =  252 *hrsPerDay
    coeffMap=  {
            '1d' :1,
            '1h' :hrsPerDay,
            '30m' :hrsPerDay *2,
            '15m' :hrsPerDay *4,
            '5m' :hrsPerDay *12,
            '3m' :hrsPerDay *20,
            '1m' :hrsPerDay *60,
            }
    coeff *=  coeffMap[interval]
    coeff  = math.sqrt(coeff)
    history = HistoryFutu() if isHK else HistoryYahoo()
    window_days = 3
    window      =150
    history.getKLineOnline(code,days,interval=interval)

    df  = history.df_
    N = df.index.size
    dfAaux = pd.Series(np.arange(N))
    dfAaux.index = df.index
    #return [f(o,c,h,l)*coeff for f in g_hv_funcs]
    dfOut  = pd.DataFrame()
    for f in g_hv_funcs:
        def auxWindowFunc(x):
            b = int(x[0])
            e = int(x[-1])
            df2 =df[b:e]
            o,h,l,c,v = history.ohlcv(df2)
            return f(o,c,h,l)*coeff
        z = dfAaux.rolling(window=window ,min_periods=window).apply(auxWindowFunc,raw=True)
        dfOut[f.__name__] = z
        pass
    return dfOut

def intervalTimeCoeff(interval, isHK=False):
    hrsPerDay = 5.5 if isHK else 6.5
    coeff =  252
    coeffMap=  {
            '1d' :1,
            '1h' :hrsPerDay,
            '30m' :hrsPerDay *2,
            '15m' :hrsPerDay *4,
            '5m' :hrsPerDay *12,
            '3m' :hrsPerDay *20,
            '1m' :hrsPerDay *60,
            }
    coeff *=  coeffMap[interval]
    coeff  = math.sqrt(coeff)
    return coeff, hrsPerDay

class VolatilityCone:
    log = logging.getLogger("main.VolatilityCone")
    def __init__(self,code,interval='5m',isHK =False):
        self.code_ = code
        self.interval_ = interval
        self.isHK_ = isHK
        self.history_ = HistoryFutu() if isHK else HistoryYahoo()
        self.df5m_ = None
        self.df1h_ = None
        self.dfOut_  = pd.DataFrame()
        pass
    def getHistory(self):
        maxDays5m = 59
        maxDays1h = 729
        if self.isHK_:
            maxDays5m = 365 * 1
            maxDays1h = 365 * 2

        self.history_.getKLineOnline(self.code_,maxDays5m,interval='5m')
        self.df5m_ = self.history_.df_
        self.history_.getKLineOnline(self.code_,maxDays1h,interval='1h')
        self.df1h_= self.history_.df_
        pass

    def rolling(self,windowDays, hvFunc=hv_GarmaanKlass):
        coeff, hrsPerDay = intervalTimeCoeff(self.interval_,self.isHK_)
        window = hrsPerDay * windowDays
        df  = None
        if self.df5m_ is None or self.df1h_ is None:
            self.getHistory()
        if self.interval_ == '5m':
            window *= 12
            df  = self.df5m_
        elif self.interval_ == '1h':
            window  = int(window)
            df  = self.df1h_
        else:
            assert False
        window  = int(window)
        N = df.index.size
        dfAaux = pd.Series(np.arange(N))
        dfAaux.index = df.index
        #return [f(o,c,h,l)*coeff for f in g_hv_funcs]
        def auxWindowFunc(x):
            b = int(x[0])
            e = int(x[-1])
            df2 =df[b:e]
            '''
            if self.interval_ == '1h':
                display(df2); sys.exit(0)
            '''
            o,h,l,c,v = self.history_.ohlcv(df2)
            return hvFunc(o,c,h,l)*coeff
        z = dfAaux.rolling(window=window ,min_periods=window).apply(auxWindowFunc,raw=True)
        return z,z[z.size-1]

    def cone_V1(self,hvFunc,ax):
        X     = ['1d','3d','1w','2w','1mon', '2mon','4mon','0.5y','1y']
        Xdays = [1,3,5,10,20,40,80,120,250]
        sigma_1d = 0.0
        sigma_3d = 0.0
        for i in range(0,len(X)):
            z,sigma = vCone.rolling(Xdays[i],hvFunc)
            if i == 0:
                sigma_1d = sigma
            if i == 1:
                sigma_3d = sigma
            self.dfOut_[X[i]] = z.describe()
        self.dfOut_ .T[ ['max', 'mean' , '25%' , '50%' , '75%' ,'min' ] ].  plot(ax=ax)
        ax.set_title(f'VC::{self.code_}:{hvFunc.__name__},HV (1d:{sigma_1d},3d:{sigma_3d}')
        pass

    def cone_V2(self,hvFunc,ax):
        '''
        Only get quantile of current volatility
        '''
        def qNearest(input,data=None, q=None):
            q = data.quantile(np.arange(0.05,1.05,0.05)) if data is not None else q
            idxSorted = (q - input).abs().argsort().iloc[:1]
            return q.iloc[idxSorted].index[0]

        label = hvFunc.__name__
        X     = ['1d','3d','1w','2w','1mon', '2mon','4mon','0.5y','1y']
        Xdays = [1,3,5,10,20,40,80,120,250]
        qList = []
        sigma_1d = 0.0
        sigma_3d = 0.0
        for i in range(0,len(X)):
            z,sigma = vCone.rolling(Xdays[i],hvFunc)
            q = qNearest(sigma,z) if not np.isnan(sigma) else -1
            qList.append(q)
            if i == 0:
                sigma_1d = sigma
            if i == 1:
                sigma_3d = sigma
            dbgStr = f'+{label}:sigma:{sigma},q:{q},X:{X[i]} '
            if X[i] == '1mon':
                self.log.warning(dbgStr)
            else:
                self.log.debug(dbgStr)
        self.log.debug(f'+{label}:plot ')
        plt.plot(X,qList,label=label)
        #ax.set_title(f'VC::{self.code_}:{hvFunc.__name__},HV (1d:{sigma_1d},3d:{sigma_3d}')
        pass

    def cone(self):
        fig = plt.figure(figsize = (12,8))
        ax = fig.add_subplot(111)  # 创建子图1
        ax.set_title(f'HVC::{self.code_}')
        for f in g_hv_funcs:
            self.cone_V2(f,ax)
        self.log.debug(f'plot show ')

        '''
        hvFunc  = hv_GarmaanKlass
        ax = fig.add_subplot(221)  # 创建子图1
        self.cone_(hvFunc,ax)

        hvFunc  = hv_ewma
        ax = fig.add_subplot(222)  # 创建子图1
        self.cone_(hvFunc,ax)

        hvFunc  = hv_YangZhang2000
        ax = fig.add_subplot(223)  # 创建子图1
        self.cone_(hvFunc,ax)

        hvFunc  = hv_Parksinson1980
        ax = fig.add_subplot(224)  # 创建子图1
        self.cone_(hvFunc,ax)
        '''


        plt.ylim(-0.01,1)
        plt.legend()
        plt.show()

    pass


if __name__ == '__main__':
    logInit()
    #vCone = VolatilityCone('TSLA')
    #vCone = VolatilityCone('ABNB')
    code = sys.argv[1] if len(sys.argv)> 1 else 'SPY'
    isHK = code.startswith('HK.')
    #vCone = VolatilityCone(code,'1h',isHK)
    vCone = VolatilityCone(code,'5m',isHK)
    vCone.cone()
    sys.exit(0)
    vCone.rolling(3,'5m')
    vCone.rolling(3,'1h')

    df = t_interval2('ABNB')

    #display(df); sys.exit(0)
    stdErr(); sys.exit(0)
