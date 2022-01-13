#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''

#from scipy.stats import pearsonr, spearmanr
import numpy as np
import matplotlib.pyplot as plt
#from numpy.core.fromnumeric import mean
from scipy import stats
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm
#from statsmodels.tsa.stattools import adfuller

import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime, timedelta
import sys,time,inspect,os
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f'../{parentdir}')
sys.path.insert(0, parentdir)
from Log import logInit
from pyhocon import ConfigFactory
import hashlib,json
import click,logging

from common.BigPandasTable import load_merged_data

class OLS:
    log = logging.getLogger("main.OLS")
    def __init__(self,df, dfPairs,windowsize=800):
        self.df_ = df
        self.dfPairs_ = dfPairs
        self.windowsize_ = windowsize
        display(self.df_.head(1))
        display(self.df_.tail(1))
        pass
    def run(self):
        oList = []
        cnt = 1
        totalN = self.dfPairs_.shape[0]
        for index,row in self.dfPairs_.iterrows():
            df = self.df_.tail(self.windowsize_)
            x = row.n1
            y = row.n2
            o,_ = self.regressOneWindow(x,y,df)
            # print(f'{cnt}/{totalN}t:\t', end='')
            oList.append(o)
            cnt  += 1
        dfZ = pd.DataFrame(oList)
        self.dfPairs_ = pd.concat([dfZ, self.dfPairs_,],axis=1)
        self.dfPairs_ = self.dfPairs_[self.dfPairs_.slope > 0.05]
        return self.dfPairs_ 

    @classmethod
    def regressOneWindow(cls, n1,n2,df):
        X1,Y = df[n1].close, df[n2].close
        #res = stats.linregress(X, Y); print(res)
        X = sm.add_constant(X1)
        model = sm.OLS(Y,X)
        res = model.fit()
        coeff = res.params
        #print(res.params)
        #print(res.summary())
        slope = coeff.close
        intercepter = coeff.const
        diff = X1 * slope + intercepter -Y
        mean = diff.mean()
        std  = diff.std()
        o = { 'slope' : slope, 'intercepter': intercepter, 'mean' : mean, 'std': std }
        o['halflife'] = cls.getHalflife(diff)
        return o,diff

    @classmethod
    def getHalflife(cls,s):
        s_lag = s.shift(1)
        s_lag.iloc[0] = s_lag.iloc[1]
        s_ret = s - s_lag
        s_ret.iloc[0] = s_ret.iloc[1]
        
    #     s_lag2 = sm.add_constant(s_lag)
    #     model = sm.OLS(s_ret,s_lag2)
    #     res = model.fit()
    #     # print(res.summary())
    #     halflife = round(-np.log(2) / list(res.params)[1],0)
        res = stats.linregress(s_lag, s_ret)
        halflife = round(-np.log(2) /res.slope,2)
        return halflife
                     

    pass

@click.command()
@click.argument('bigcsv')
@click.argument('pairscsv')
@click.argument('dst')
@click.option('--windowsize',  help='', default=500)
def ols(bigcsv,pairscsv, dst,windowsize):
    logInit()
    df,symbols = load_merged_data(bigcsv)
    dfPairs = pd.read_csv(pairscsv)

    olsRegress  = OLS(df,dfPairs,windowsize)
    df = olsRegress.run()
    df.to_csv(dst,index=False)
    display(df.tail(10))
    olsRegress.log.debug(f'Wrote {dst}')
    pass

@click.command()
@click.argument('n1')
@click.argument('n2')
@click.argument('bigcsv')
@click.argument('pairscsv')
@click.option('--windowsize',  help='', default=500)
def plot(n1,n2, bigcsv,pairscsv, windowsize):
    logInit()
    df,symbols = load_merged_data(bigcsv)
    dfPairs = pd.read_csv(pairscsv)
    df = df.tail(windowsize)
    row = dfPairs[dfPairs.pair == f'{n1}_{n2}'].iloc[0]

    std = row['std'].astype(float)
    mean = row['mean'].astype(float)
    slope = row.slope.astype(float)
    intercepter = row.intercepter.astype(float)
    diff = df[n1].close * slope + intercepter - df[n2].close

    fig = plt.figure(figsize = (12,8))
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    ax = fig.add_subplot(111)
    diff.plot(ax=ax)
    ax.axhline(mean+std*2, color='g', linestyle='--', label= f'Sell {n1}/Buy {n2}')
    ax.axhline(mean-std*2, color='r', linestyle='--', label= f'Buy {n1}/Sell {n2}')
    ax.axhline(mean-std, color='y', linestyle='--')
    ax.axhline(mean+std, color='y', linestyle='--')
    ax.axhline(mean,  linestyle='--')
    ax.set_title(f'+:{n1} short {n1}+ long {n2};-:short {n2}+ long {n1};')
    plt.legend()
    plt.show()

    pass




@click.group()
def cli():
    pass


if __name__ == '__main__':
    cli.add_command(ols)
    cli.add_command(plot)
    cli(); sys.exit(0)


    '''
    from scipy import stats
from statsmodels.tsa.stattools import adfuller
import pandas as pd
from datetime import datetime, timedelta
def load_merged_data(file = 'data.cn/20211222.csvx'):
    msg  = f'pd.read_csv({file}, index_col=0, header=[0,1], parse_dates=True )'
    #print(msg)
    df  = pd.read_csv(file, index_col=0, header=[0,1], parse_dates=True )
    df = df[ ~ df.isna().any(axis=1)]
    symbols = ','.join(set([c[0] for c in df.columns]))
    return df,symbols
df,symbols = load_merged_data('./gw/test.csv')
start = datetime.now() - timedelta(days=1)
df = df[df.index >start]
#display(df.head(1))

                     
    
    
    
    
    
    
    '''

