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


def CDF_Hart1968(x):
    '''
        from scipy.stats import norm
        yNS = norm.cdf(x)
    '''
    a1 = 0.0352624965998911
    a2 = 0.700383064443688
    a3 = 6.37396220353165
    a4 = 33.912866078383
    a5 = 112.079291497871
    a6 = 221.213596169931
    a7 = 220.206867912376

    b1 = 0.0883883476483184
    b2 = 1.75566716318264
    b3 = 16.064177579207
    b4 = 86.7807322029461
    b5 = 296.564248779674
    b6 = 637.333633378831
    b7 = 793.826512519948
    b8 = 440.413735824752
    y = abs(x)
    A =(((( (a1 *y +a2)*y  +a3)*y +a4 )*y +a5 )*y +a6)*y +a7
    B =((((( (b1 *y +b2)*y  +b3)*y +b4 )*y +b5 )*y +b6)*y +b7) * y +b8
    C = y + 1/(y+2*(y+3*(y+4*(y+0.65))))
    NC = 0
    if y < 7.07106781186547:
        NC = math.exp(-y **2 /2) * A /B
    elif y <= 37:
        NC = math.exp(-y **2 /2) /(2.506628274631 *C)
    else: # > 37
        NC = 0
    if x > 0:
        NC = 1 - NC
    return NC
CDF_Hart1968 = np.frompyfunc(CDF_Hart1968,1,1)

Lim = 6
x = np.linspace(-Lim, Lim ,1000)
yN = CDF_Hart1968(x)
yNS = norm.cdf(x)

xpercent = np.linspace(0, 1 ,1000)
yppf     = norm.ppf(xpercent)


fig = plt.figure(figsize = (12,8))
ax = fig.add_subplot(1,1,1)  # 创建子图1
#ax.plot(x,yN, 'b-', lw=2, alpha=0.6, label='N')
#ax.plot(yNS,x, 'b-', lw=2, alpha=0.6, label='N')
ax.plot(xpercent,yppf, 'r-', lw=2, alpha=0.6, label='N')
ax.grid()
#ax.plot(x,yNS, 'r-', lw=2, alpha=0.6, label='NS')
plt.show()


