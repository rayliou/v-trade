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
    sigma = math.sqrt(sigma_sqare)
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
from DataDownloadFutu import DataDownloadFutu

g_funcs = [
        hv_Parksinson1980,
        hv_GarmaanKlass,
        hv_YangZhang2000,
        hv_ewma,
        ]

def t_period(period):
    global g_funcs
    stock  ='HK.00700'
    d  = DataDownloadFutu()
    #5.5 hours per day
    coeff = 5.5  * 252
    if period == '1M':
        df = d.readKLineFromCsv(stock,KLType.K_1M)
        coeff*= 60
        pass
    elif period == '5M':
        df = d.readKLineFromCsv(stock,KLType.K_5M)
        coeff*= 12
        pass
    else:
        assert False
    coeff = math.sqrt(coeff)
    o,c,h,l = df.open,df.close, df.high,df.low
    return [f(o,c,h,l)*coeff for f in g_funcs]

def t():
    global g_funcs
    df  = pd.DataFrame()
    df['5M'] = t_period('5M')
    df['1M'] = t_period('1M')
    df['idx'] = [f.__name__ for f in g_funcs]
    df.set_index('idx',inplace=True)
    display(df)
    pass

if __name__ == '__main__':
    t();sys.exit()
    file = 'b.data/HK.00700.K1M.csv'
    df = pd.read_csv(file,index_col=0,parse_dates=True)
    df['h_shift'] = df.high.shift()
    df['h_shift_-1'] = df.high.shift(-1)

    #display(df); sys.exit(0)
    stdErr(); sys.exit(0)
