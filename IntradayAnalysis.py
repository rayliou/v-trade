#!/usr/bin/env python3
# coding=utf-8


from IPython.display import display, HTML
from DataDownloadFutu import DataDownloadFutu
from futu import *
d = DataDownloadFutu()
code  = 'HK.03690'
code  = 'HK.00700'
df  = d.getKLine(code,KLType.K_1M,59)
import matplotlib.pyplot as plt
import numpy as np
by = lambda idx : idx.date
def HLtime(df):
    h = df.high.max()
    l = df.low.min()
    H = df [np.isclose(df.high,h)].index[0].time()
    L = df [np.isclose(df.low,l)].index[0].time()
    H = H.hour * 60 + H.minute
    L = L.hour * 60 + L.minute
    return pd.Series([H,L])


dfTM = df.groupby(by=by).apply(HLtime)
dfTM.columns = ['H', 'L']
dfTM
display(dfTM.H[0])
#df['tm'] = df.index.time
fig = plt.figure(figsize = (12,8))
ax = fig.add_subplot(111)
dfTM.hist(bins=60*5,ax=ax)
#dfTM.L.hist(bins=60,ax=ax)
plt.legend()
plt.show()
