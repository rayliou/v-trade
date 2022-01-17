#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''

import sys,time,inspect,os,logging
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f'../{parentdir}')
sys.path.insert(0, parentdir)
from Log import logInit
import pandas as pd
from datetime import timedelta,datetime
import numpy as np
from IPython.display import display, HTML
from statsmodels.tsa.stattools import coint

from common.BigPandasTable import load_merged_data


class Study:
    log = logging.getLogger("main.Study")
    # days = [28,5,7,14,3]
    days = [5,7,10,14]
    def __init__(self):
        pass

    def loadData(self, bigcsv = '/Users/henry/stock/v-trade/data/data_test/stk-merged-20220114.cn.Yahoo.csv'):
        df,symbols = load_merged_data(bigcsv)
        self.symbols_ = symbols
        self.df_ = df
        self.dfO_ = None
        self.dtList_ = np.unique((df.index + timedelta(days=1)).date)
        self.log.debug(f'{symbols}')
        self.log.debug(df.head(1))
        self.log.debug(df.tail(1))
        #self.log.debug(self.dtList_)
        pass
    def outputData(self, retcsv = '/Users/henry/stock/v-trade/data/data_test/studyCoint-pairs-20220114.cn.Yahoo.csv'):
        if self.dfO_ is None:
            return
        self.dfO_.to_csv(retcsv, index=False)
        self.log.debug(f'Wrote: {retcsv}')
        pass
    def run(self):
        days = self.days
        # self.symbols_ = ['GOTU','LU']
        symList = self.symbols_
        N = len(self.symbols_)
        #loop
        pPairs = []
        dfO = None
        cnt  = 0
        totalCnt =  int(N *(N-1) /2)
        for i in range(N):
            for j in range(i+1,N):
                cnt += 1
                k1 = symList[i]
                k2 = symList[j]
                self.log.debug(f'[{cnt}/{totalCnt}]:\t{k1} {k2}')
                df = self.resampleGetCoints_v1(k1,k2)
                if df is None:
                    continue
                display(df)
                dfO = df if dfO is None else pd.concat([dfO, df])
                self.log.debug(dfO)
        self.dfO_ = dfO
        pass
    def getCoint(self,n1,n2, end,d):
        startx2 = end -timedelta(days=d*2)
        start = end -timedelta(days=d)
        self.log.debug(f'd:{d},start:{start},startx2:{startx2}')
        Xx2 = self.df_[startx2:end][n1].close
        Yx2 = self.df_[startx2:end][n2].close
        X = self.df_[start:end][n1].close
        Y = self.df_[start:end][n2].close
        self.log.debug(f'Xx2:{Xx2.index[0]}:{Xx2.index[-1]}')
        # self.log.debug(f'{Yx2.index[0]}:{Yx2.index[-1]}')
        # self.log.debug(f'{X.index[0]}:{X.index[-1]}')
        # self.log.debug(f'{Y.index[0]}:{Y.index[-1]}')

        _, pCoinx2, _ = coint(Xx2, Yx2)
        _, pCoin, _ = coint(X, Y)
        p = max(pCoinx2, pCoin)
        o = {'pairs': f'{n1}_{n2}', 'p': p, 'end':end, 'startx2':startx2, 'start':start, 'd':d}
        # self.log.debug(o)
        return o

    def resampleGetCoints_v2(self,n1,n2,threshhold=0.05):
        ''' 给定end日期, 对于days 的每个day, 取 mean( from 5 to day) 最小
        '''
        pass
    def resampleGetCoints_v1(self,n1,n2,threshhold=0.05):
        '''
        单双周期均满足       
        '''
        df = self.df_
        dtList = self.dtList_
        # self.log.debug(f'dtList:{dtList}')
        # self.log.debug(f'{dtList[10-1:]}')
        oList = []
        for d in self.days:
            #slide the window
            for end in dtList[d*2-1:]:
                # self.log.debug(f'end:{end}')
                o = self.getCoint(n1,n2,end ,d)
                if o['p'] > threshhold:
                    continue
                oList.append(o)
        if len(oList) == 0:
            return None
        return pd.DataFrame(oList)

    def resampleGetCoints_v0(self,n1,n2):
        df = self.df_
        oList = []
        threshhold = 0.05
        dtList = self.dtList_
        for d in self.days:
            #slide the window
            for end in dtList[d-1:]:
                start = end -timedelta(days=d)
                o = self.getCoint(n1,n2,start,end,d,d)
                if o['p'] > threshhold:
                    return None
                oList.append(o)
                self.log.debug(o)
                #compared with the small windws: from 2 days to d-1
                for n in range(2,d):
                    start = end -timedelta(days=n)
                    o = self.getCoint(n1,n2,start,end,d,n); oList.append(o)
                    # self.log.debug(o)
        return pd.DataFrame(oList)


import click,logging
@click.command()
@click.argument('bigcsv')
@click.argument('dst')
def studycointegrate(bigcsv,dst):
    s = Study()
    # s.days = [28,5,3]
    # s.days = [3,]
    s.loadData(bigcsv)
    s.run()
    s.outputData(dst)
    pass

@click.command()
@click.argument('bigcsv')
@click.option('--skipdays',  help='', default=28)
def date_list_from_bigcsv(bigcsv,skipdays):
    df,symbols = load_merged_data(bigcsv)
    start = df.index[0] + timedelta(days=skipdays)
    df = df[start:]
    dtList = np.unique((df.index + timedelta(days=1)).strftime('%Y-%m-%d'))
    # dtList = np.unique(df.index.date)
    print('\n'.join(dtList))

    pass

@click.group()
def cli():
    pass


if __name__ == '__main__':
    logInit()
    cli.add_command(studycointegrate)
    cli.add_command(date_list_from_bigcsv)
    cli(); sys.exit(0)