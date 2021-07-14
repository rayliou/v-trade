#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
import numpy as np
import matplotlib.pyplot as plt


'''
https://qsctech-sange.github.io/option-price
https://github.com/QSCTech-Sange/Options-Calculator/blob/master/Backend/Option.py
pip install option-price

- https://numpy.org/doc/stable/user/index.html
- https://numpy.org/doc/stable/reference/generated/numpy.linspace.html
- https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
- https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
- Breakeven Point 盈亏平衡点

蒙特卡洛 American Option Price Boyle, Broadie Glasserman[1997] by Meier(2000)
'''

def BG(CallPutFlag, S,X,T,r,b, Sig,m, Branches, nSimulations):
    z  = 1 if CallPutFlag == 'CALL' else -1
    Drift  = (b-Sig ** 2/2 )* T /(m-1)
    SigSqrdt = Sig * sqrt(T/(m-1))
    Discdt = exp(-r*T/(m-1))
    for Estimator in range(1,2):
        EstimatorSum = 0
        for simulation in range(1,nSimulations):





    pass

class OptionBroadieGlasserman:
    CALL = 0
    PUT  = 1
    def __init__(self, k, premium,delta = 0.5, t=1, opType=CALL):
        pass
    pass

if __name__ == '__main__':
    coveredCall()
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
