#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
import numpy as np
import matplotlib.pyplot as plt


from GBSOptionPricing import american,amer_implied_vol

# def american(option_type, fs, x, t, r, q, v): # American Options (stock style, set q=0 for non-dividend paying options)
# def amer_implied_vol(option_type, fs, x, t, r, q, cp):

p = american('p', 654 ,655, 1/12.0, 0.01, 0, 0.52784)
print(p)
amer_implied_vol('p', 654 ,655, 1/12.0, 0.01, 0, 39.8049)


'''
https://qsctech-sange.github.io/option-price
https://github.com/QSCTech-Sange/Options-Calculator/blob/master/Backend/Option.py
pip install option-price

- https://numpy.org/doc/stable/user/index.html
- https://numpy.org/doc/stable/reference/generated/numpy.linspace.html
- https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
- https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
- Breakeven Point 盈亏平衡点
'''

class Option:
    CALL = 0
    PUT  = 1
    def __init__(self, k, premium,delta = 0.5, t=1, opType=CALL):
        self.type_ = opType
        self.k_ = k
        self.premium_ = premium
        self.delta_ = delta
        self.t_ = t
        pass
    def b(self,s):
        return self.price(s)
    def s(self,s):
        return -self.price(s)


    def price(self,s):
        return self.priceCall(s) if self.type_ == Option.CALL else self.pricePut(s)

    def priceCall(self,s):
        g  = -self.premium_
        if s < self.k_:
            return g
        #FIXME
        g += (s - self.k_) * self.delta_
        return g

    def pricePut(self,s):
        g  = -self.premium_
        if s > self.k_:
            return g
        #FIXME
        g += (self.k_ -s ) * self.delta_
        return g
    pass
def ironCondor():
    p1 = Option(670,30,0.2,opType=Option.PUT)
    p2 = Option(680,35,0.3,opType=Option.PUT)
    c3 = Option(800,30,0.3,opType=Option.CALL)
    c4 = Option(810,20,0.2,opType=Option.CALL)

    z =np.linspace(0,1000,1000)
    y = []
    for i in z:
        g = 0
        g += p1.b(i)
        g += p2.s(i)
        g += c3.s(i)
        g += c4.b(i)
        y.append(g)
        #y.append(o1.price(i)- o2.price(i))
    #g=plt.plot(x,y,'^k:',label='yyyy')
    plt.plot(z,y,'r--',label='yyyy')
    #plt.plot(z,0,'b--',label='0')
    plt.xlabel('price s')
    plt.ylabel('option price')
    plt.legend()
    plt.show()

def coveredCall():
    c1 = Option(133,2.07,0.558,opType=Option.CALL)
    c2 = Option(134,1.54,0.377,opType=Option.CALL)
    c3 = Option(135,1.13,0.468,opType=Option.CALL)
    s0 = 132.15 + 0.35
    #s1 = 133
    rate = 0.05
    z =np.linspace(s0 *(1-rate),s0*(1+rate),50)
    y1 = []
    y2 = []
    y3 = []
    for i in z:
        s = i - s0
        y1.append(s+c1.s(i)/c1.delta_)
        y2.append(s+c2.s(i)/c2.delta_)
        y3.append(s+c3.s(i)/c3.delta_)
        #y.append(o1.price(i)- o2.price(i))
    #g=plt.plot(x,y,'^k:',label='yyyy')
    plt.plot(z,y1,'r-',label='133')
    plt.plot(z,y2,'g--',label='134')
    plt.plot(z,y3,'b--',label='135')
    #plt.plot(z,0,'b--',label='0')
    plt.xlabel('price s')
    plt.ylabel('option price')
    plt.legend()
    plt.show()

from futu import *
from DataDownloadFutu import DataDownloadFutu
from UserSecurity import UserSecurity

def downloadAllOptionHKSecurities():
    us = UserSecurity()
    d = DataDownloadFutu()
    df =us.getSecuritiesList('optionHK')[['code', 'name']]
    dfRet = pd.DataFrame()
    for r in df.iterrows():
        num = r[0]
        name = f'{r[1][1]}@{r[1][0]}'
        code = r[1][0]
        dfO = d.getKLine(code, ktype=KLType.K_60M ,days=2*365)[['open','high','low','close','volume']]
        if dfRet.index.size ==0:
            dfRet  = dfO.add_suffix(f'_{name}')
        else:
            dfRet = pd.merge_asof(dfRet, dfO, right_index=True, left_index=True, suffixes=('',f'_{name}'))
        print(f'finish {num} {name} ')
        if num == 3:
            display(dfRet)
        pass
    print("to_csv('./optionHK_securities_1h.csv'")
    d.close()
    dfRet.to_csv('./optionHK_securities_1h.csv')
    print("Done:to_csv('./optionHK_securities_1h.csv'")
    pass

downloadAllOptionHKSecurities();sys.exit(0)

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
df = pd.read_csv('./optionHK_securities_1h.csv',index_col=0)
fig = plt.figure(figsize = (12,8))

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']


ax = fig.add_subplot(111)
ax = sns.heatmap(df.corr(),ax=ax)
plt.show()

if __name__ == '__main__':
    #coveredCall()
    pass
    #ironCondor()

'''

some_option = Option(european=False,
                    kind='put',
                    s0=27.8,
                    k=33,
                    sigma=0.428,
                    r=0.01, start='2021-06-26', end='2021-07-29', dv=0)

x = some_option.getPrice()
y = some_option.getPrice(method='MC',iteration = 500000)
z = some_option.getPrice(method='BT',iteration = 10000)
x,y,z
'''
