#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''

#from scipy.stats import pearsonr, spearmanr

from IPython.display import display, HTML
from datetime import datetime, timedelta
from scipy import stats
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys,time,inspect,os,re
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f'../{parentdir}')
sys.path.insert(0, parentdir)
from Log import logInit
from pyhocon import ConfigFactory
import hashlib,json
import click,logging

from common.BigPandasTable import load_merged_data

class PositionPair:
    log = logging.getLogger("main.PositionPair")
    positions = dict()
    profits = []
    def __init__(self, n1,n2,price1,price2,pos1,pos2,ext):
        self.n1_ = n1
        self.n2_ = n2

        self.price1_ = price1
        self.price2_ = price2

        self.pos1_ = pos1
        self.pos2_ = pos2

        self.cap1_ = pos1 *price1
        self.cap2_ = pos2 * price2

        self.ext_  = ext
        self.z0_   = ext['z']
        pass
    def __repr__(self):
        s1 = f'{self.n1_}\t<cap:{self.pos1_*self.price1_},price:{self.price1_},pos:{self.pos1_}>\n'
        s2 = f'{self.n2_}\t<cap:{self.pos2_*self.price2_},price:{self.price2_},pos:{self.pos2_}>;'
        return s1 +s2 + str(self.ext_)
    @classmethod
    def new(cls, n1,n2,price1,price2,pos1,pos2, ext):
        p = f'{n1}_{n2}'
        assert p not  in cls.positions
        position = PositionPair(n1,n2,price1,price2,pos1,pos2,ext)
        cls.positions[p] = position
        return position
    @classmethod
    def close(cls,n1,n2, price1, price2, ext):
        p = f'{n1}_{n2}'; assert p in cls.positions
        position =  cls.positions[p]
        profit = dict()
        rt =  (price1 - position.price1_) * position.pos1_  + (price2 - position.price2_) * position.pos2_
        dz = ext['z'] - position.z0_


        o = {'pair': p, 'rt':rt, 'dz':dz}
        o['z0'] = position.z0_
        o['z'] = ext['z']
        o['std_xy_percent'] = 100.* ext['std']/max(position.price1_,position.price2_)
        o['rt'] = o['rt'] /max(abs(position.cap1_),abs(position.cap2_)) * 100.
        o['model_date'] = ext['model_date']
        cls.log.warning(o)
        del cls.positions[p]
        cls.profits.append(o)
        return 0

class BT:
    log = logging.getLogger("main.BT")
    def __init__(self,df):
        self.df_ =  df
        #display(self.df_.head(1))
        #display(self.df_.tail(1))
        pass
    def run(self, pairscsvs):
        for file in pairscsvs:
            m = re.match(r'.*(20[-0-9]+)\.(.*)/ols.csv' , file)
            assert len(m.groups()) == 2 , f'Path format is error :{file}'
            modelDate,g = m.groups()
            dfOLS = pd.read_csv(file)
            totalPairs = dfOLS.shape[0]
            cnt = 1
            for idx,rowPair in dfOLS.iterrows():
                self.log.debug(f'btOnePair({rowPair.pair},{g},{modelDate}')
                self.btOnePair(rowPair,g,modelDate, totalPairs, cnt)
                cnt += 1

    def btOnePair(self,rowPair, group,modelDate,totalPairs, cnt):
        
        df = self.df_
        self.log.debug(f'[{cnt}/{totalPairs}]\tmodelDate:{modelDate}')
        # display(df[modelDate:])
        #np.unique((df[curDate:].index + timedelta(days=1)).strftime('%Y-%m-%d'))
        dateList = np.unique(df[modelDate:].index.strftime('%Y-%m-%d'))
        size = len(dateList)
        assert size >= 2, f'dateList must >= 2 {dateList};modelDate={modelDate}, group={group}'
        # display(rowPair)
        df = df[dateList[1]:] if size < 3 else df[dateList[1]:dateList[2]]

        n1,n2 = rowPair.pair.split('_')
        if n1 == 'FUTU' or n2 == 'FUTU':
            return
        cDate = df.index[0].day
        zPrev = 0
        for idx,r in df.iterrows():
            next_day = 1 if idx.day != cDate else 0
            x = r[n1].close
            y = r[n2].close
            diff = x *rowPair.s + rowPair.i - y
            z = (diff - rowPair.m)/rowPair.st
            p = f'{n1}_{n2}'
            position = PositionPair.positions[p] if p in PositionPair.positions else None
            ext = {'tm':idx, 'z':z,'next_day':next_day, 'std': rowPair.st }
            ext['model_date'] = modelDate
            #self.log.debug(ext)
            if next_day == 1:
                if position is not None:
                    self.log.debug(f'[{cnt}/{totalPairs}]\t[{modelDate}][{idx}]:Next day')
                    PositionPair.close(n1,n2,x,y,ext)
                break
            if position is None:
                if (zPrev < 0 and z < zPrev) or (zPrev > 0 and z > zPrev):
                    self.log.debug(f'[{cnt}/{totalPairs}]\t[{modelDate}][{idx}]Trail far z:{z},zPrev:{zPrev},')
                    zPrev =z
                    continue
                if z < -2 :
                    position = PositionPair.new(n1,n2,x,y,100*rowPair.s, -100,ext)
                    self.log.info(f'[{cnt}/{totalPairs}]\t[{modelDate}][{idx}]New Position z:{z},zPrev:{zPrev},')
                elif z > 2:
                    position = PositionPair.new(n1,n2,x,y,-100*rowPair.s, 100 ,ext)
                    self.log.info(f'[{cnt}/{totalPairs}]\t[{modelDate}][{idx}]New Position z:{z},zPrev:{zPrev},')

            else:
                z0 = position.z0_
                #stop !!!!!!!
                if ((z0 < 0) and (z - z0) < -1.0) or ((z0 > 0) and (z - z0) > 1.0):
                    ext['stop'] = 1
                    self.log.debug('[{cnt}/{totalPairs}]\t[{modelDate}][{idx}]Stop losss')
                    PositionPair.close(n1,n2,x,y,ext)
                #Trailling
                elif ((z0 < 0) and (z > zPrev) ) or ((z0 > 0) and (z < zPrev) ):
                    self.log.debug(f'[{cnt}/{totalPairs}]\t[{modelDate}][{idx}]Trail near z0:{z0}; z:{z},zPrev:{zPrev},')
                    zPrev =z
                    continue
                elif ((z0 < 0) and (z - z0) > 1.0) or ((z0 > 0) and (z - z0) < -1.0):
                    ext['stop'] = 0
                    self.log.debug(f'[{cnt}/{totalPairs}]\t[{modelDate}][{idx}]Close with  z0:{z0}; z:{z},zPrev:{zPrev},')
                    PositionPair.close(n1,n2,x,y,ext)
            zPrev = z
            pass
        return df



@click.command()
@click.argument('bigcsv')
@click.argument('pairscsvs', nargs=-1)
@click.argument('dst')
def m_bt(bigcsv,pairscsvs, dst):
    '''
    BT data range : 2021-12-16:2022-01-13
    model data range:
    '''

    logInit()
    #bigcsv = '/Users/henry/stock/v-trade/data/data_study/stk-daily-20220113.cn.Yahoo.30s.csv'
    #olscsv = '/Users/henry/stock/env_study/2022-01-12.cn/ols.csv'
    df,symbols = load_merged_data(bigcsv,verifyDays=20)
    #modelDate = '20211223'
    b = BT(df)
    b.run(pairscsvs)
    if len(PositionPair.profits) == 0:
        return

    df = pd.DataFrame(PositionPair.profits)
    display(df)
    df.to_csv(dst)
    b.log.debug(f'Wrote {dst}')
    m  = df.rt.mean()
    std  = df.rt.std()
    sr   = m/std
    print(f'm:{m}; std:{std},sr:{sr}')
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

    std = row['st'].astype(float)
    mean = row['m'].astype(float)
    slope = row.s.astype(float)
    intercepter = row.i.astype(float)
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
    # bt2();sys.exit(0)
    cli.add_command(m_bt)
    cli.add_command(plot)
    cli(); sys.exit(0)
