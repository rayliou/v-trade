#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
import numpy as np
import matplotlib.pyplot as plt


from GBSOptionPricing import american_76,american,amer_implied_vol
# https://quantlib-python-docs.readthedocs.io/en/latest/dates.html
import QuantLib as ql
import scipy.stats as sps


def QuantLibOptionPrice(option_type, fs, x, t, r, q, v,start,end):
    '''
        American Option Pricing with QuantLib and Python
        http://gouthamanbalaraman.com/blog/american-option-pricing-quantlib-python.html
    '''
    # option data
    maturity_date = end
    spot_price = fs
    strike_price = x
    volatility = v
    dividend_rate =  q
    option_type = ql.Option.Call if option_type in {'c','C','call','CALL', 'Call'} else ql.Option.Put

    risk_free_rate = r
    day_count = ql.Actual365Fixed()
    calendar = ql.UnitedStates()

    startDate = start
    ql.Settings.instance().evaluationDate = startDate

    payoff = ql.PlainVanillaPayoff(option_type, strike_price)
    settlement = startDate

    am_exercise = ql.AmericanExercise(settlement, maturity_date)
    american_option = ql.VanillaOption(payoff, am_exercise)

    eu_exercise = ql.EuropeanExercise(maturity_date)
    european_option = ql.VanillaOption(payoff, eu_exercise)

    spot_handle = ql.QuoteHandle(
        ql.SimpleQuote(spot_price)
    )
    flat_ts = ql.YieldTermStructureHandle(
        ql.FlatForward(startDate, risk_free_rate, day_count)
    )
    dividend_yield = ql.YieldTermStructureHandle(
        ql.FlatForward(startDate, dividend_rate, day_count)
    )
    flat_vol_ts = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(startDate, calendar, volatility, day_count)
    )
    bsm_process = ql.BlackScholesMertonProcess(spot_handle,
                                            dividend_yield,
                                            flat_ts,
                                            flat_vol_ts)
    steps = 2000
    binomial_engine = ql.BinomialVanillaEngine(bsm_process, "crr", steps)
    american_option.setPricingEngine(binomial_engine)
    return american_option.NPV()

class QSCTOption:
    '''
    - https://github.com/QSCTech-Sange/Options-Calculator
    '''

    # european 为 欧式期权 (False 为欧式期权)
    # kind 看涨或看跌（Put 为 -1 , Call 为 1）
    # s0 标的资产现价
    # k 期权执行价
    # t 期权到期时间 - 现在时间,以天计
    # r 适用的无风险利率，连续复利
    # sigma 适用的波动率，
    # dv 股利信息，连续复利
    def __init__(self, european, kind, s0, k, t, r, sigma, dv):
        kind  = 1 if kind in {'c','C','call','CALL', 'Call'} else  -1
        self.european = european
        self.kind = kind
        self.s0 = s0
        self.k = k
        #年化时间
        self.t = t
        self.sigma = sigma
        self.r = r
        self.dv = dv
        self.bsprice = None
        self.mcprice = None
        self.btprice = None

    # B-S-M 计算价格方法
    def bs(self):
        if self.european or self.kind == 1:
            d_1 = (np.log(self.s0 / self.k) + (
                    self.r - self.dv + .5 * self.sigma ** 2) * self.t) / self.sigma / np.sqrt(
                self.t)
            d_2 = d_1 - self.sigma * np.sqrt(self.t)
            self.bsprice = self.kind * self.s0 * np.exp(-self.dv * self.t) * sps.norm.cdf(
                self.kind * d_1) - self.kind * self.k * np.exp(-self.r * self.t) * sps.norm.cdf(self.kind * d_2)
        else:
            self.bsprice = "美式看跌期权不适合这种计算方法"
        return self.bsprice

    # 蒙特卡罗定价
    def mc(self, iteration):
        if self.european or self.kind == 1:
            zt = np.random.normal(0, 1, iteration)
            st = self.s0 * np.exp((self.r - self.dv - .5 * self.sigma ** 2) * self.t + self.sigma * self.t ** .5 * zt)
            st = np.maximum(self.kind * (st - self.k), 0)
            self.mcprice = np.average(st) * np.exp(-self.r * self.t)
        else:
            self.mcprice = "美式看跌期权不适合这种计算方法"
        return self.mcprice

    # 二叉树定价
    def bt(self, iteration):
        delta = self.t / iteration
        u = np.exp(self.sigma * np.sqrt(delta))
        d = 1 / u
        p = (np.exp((self.r - self.dv) * delta) - d) / (u - d)

        tree = np.arange(0,iteration * 2 + 2,2,dtype=np.float128)
        tree[iteration//2 + 1:] = tree[:(iteration+1)//2][::-1]
        np.multiply(tree,-1,out=tree)
        np.add(tree,iteration,out=tree)
        np.power(u,tree[:iteration//2],out=tree[:iteration//2])
        np.power(d,tree[iteration//2:],out=tree[iteration//2:])
        np.maximum((self.s0 * tree - self.k) * self.kind,0,out=tree)

        for j in range(iteration):
            newtree = tree[:-1] * p + tree[1:] * (1 - p)
            newtree = newtree * np.exp(-self.r * delta)
            if not self.european:
                compare = np.abs(iteration - j - 1 - np.arange(tree.size - 1) * 2).astype(np.float128)
                np.power(u,compare[:len(compare)//2],out=compare[:len(compare)//2])
                np.power(d,compare[len(compare)//2:],out=compare[len(compare)//2:])
                np.multiply(self.s0,compare,out=compare)
                np.subtract(compare,self.k,out=compare)
                np.multiply(compare,self.kind,out=compare)
                np.maximum(newtree, compare,out=newtree)
            tree = newtree
        self.btprice = tree[0]
        return self.btprice




def qscOption(option_type, fs, x, t, r, q, v):
    some_option = QSCTOption(european=False,
                        kind=option_type,
                        s0=fs,
                        k=x,
                        sigma=v,
                        r=r, t=t, dv=q)

    x = some_option.bs()
    y = some_option.mc(iteration = 500000)
    z = some_option.bt(iteration = 10000)
    return f'bs={x},mc={x},bt={z}'



def t(option_type, fs, x, r, q, v,start=None,end=None):
    today = ql.Date.todaysDate()
    start =  ql.Date(start, '%Y%m%d') if start is not None else today
    end =  ql.Date(end, '%Y%m%d') if end is not None else start + ql.Period('1M')
    #print(start,end)
    calendarUS = ql.UnitedStates(ql.UnitedStates.NYSE)
    us_bdays=calendarUS. businessDaysBetween(start,end)
    T1 = us_bdays /252

    dc=ql.Business252()
    T2=dc.dayCount(start,end)
    yf=dc.yearFraction(start,end)
    t  = yf
    #print(T1,T2,yf)
    print('american              : {}'.format(american(option_type, fs, x, t, r, q, v)))
    print('american_76           : {}'.format( american_76(option_type, fs, x, t, r, v)))
    print('qscOption             : {}'.format(qscOption(option_type, fs, x, t, r, q, v)))
    print('QuantLibOptionPrice   : {}'.format(QuantLibOptionPrice(option_type, fs, x, t, r, q, v,start,end)))
    pass



if __name__ == '__main__':
    t('c', 657.49 ,710, 0.01, 0, 0.48413,start=None)
    t('c', 657.49 ,710, 0.01, 0, 0.48413,start=None,end='20210716')
    sys.exit(0)
    #ironCondor()
